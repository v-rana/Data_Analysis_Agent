from typing import Annotated
from pydantic import BaseModel
from contextlib import asynccontextmanager

import redis.asyncio as redis

from fastapi import (
    FastAPI,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from auth.simple_auth import AuthMiddleware, SimpleAuthService
from config import settings
from db.conn import get_session
from db.fetch_context import fetch_schemas, fetch_tables_under_schema
from DTO.agent_trace_layer import AgentRunResponse, build_agent_run_response 

from services.execute_agent_service import execute_agent
from services.csv_upload_service import upload_csv
from services.session_service import create_session, delete_session, get_session_context, list_sessions
from services.rate_limit_service import (
    enforce_rate_limits,
    policy_limit,
)

from helper.logger import AppLogger

logger = AppLogger(__name__)

class QueryRequest(BaseModel):
    session_id: str
    schema_name: str
    table_name: str
    user_input: str


DbSession = Annotated[AsyncSession, Depends(get_session)]

@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = redis.Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )

    try:
        await redis_client.ping()
        logger._logger.info("Redis connection established")
        app.state.redis = redis_client
        yield
    finally:
        await redis_client.aclose()
        logger._logger.info("Redis connection closed")

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")



if settings.AUTH_ENABLED:
    app.add_middleware(
        AuthMiddleware,
        auth_service=SimpleAuthService(settings.AUTH_TOKEN),
        public_paths=["/", "/health", "/sql-agent", "/static"],
    )


def get_client_ip(request: Request) -> str:
    client_ip = request.headers.get("x-real-ip")

    if not client_ip:
        raise HTTPException(
            status_code=400,
            detail="Unable to determine client IP",
        )

    return client_ip


async def enforce_agent_rate_limits(
    request: Request,
    session_id: str,
    response: Response,
) -> None:
    redis_client = request.app.state.redis
    client_ip = get_client_ip(request)

    headers = await enforce_rate_limits(
        redis_client,
        [
            policy_limit("agent_per_session_minute", session_id),
            policy_limit("agent_per_session_day", session_id),
            policy_limit("agent_per_ip_day", client_ip),
        ],
    )

    for name, value in headers.items():
        response.headers[name] = value
   
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "app": "sql_agent",
    }


@app.get("/", include_in_schema=False)
async def portfolio_page(request: Request):
    return templates.TemplateResponse(request, "portfolio.html")

@app.get("/ip")
async def get_ip(request: Request):
    return {"ip": get_client_ip(request)}

@app.get("/sql-agent", include_in_schema=False)
async def sql_agent_page(request: Request):
    return templates.TemplateResponse(request, "sql_agent.html")


@app.get("/api/get_schemas")
async def get_schema_names(db: DbSession):
    return await fetch_schemas(db)


@app.get("/api/get_table")
async def get_table_names(db: DbSession, schema: str = "public"):
    result = await fetch_tables_under_schema(db, schema)
    return result


class SessionRequest(BaseModel):
    mode: str = "personal"
    secret_key: str | None = None


@app.post("/api/session")
async def start_session(
    payload: SessionRequest,
    request: Request,
):
    client_ip = get_client_ip(request)

    await enforce_rate_limits(
            request.app.state.redis,
            [
                policy_limit("session_create_per_ip", client_ip),
            ],
        )
    return await create_session(
        request.app.state.redis,
        payload.mode,
        payload.secret_key,
    )

@app.get("/api/sessions")
async def get_sessions(
    request: Request,
    secret_key: str,
):
    sessions = await list_sessions(
        request.app.state.redis,
        secret_key,
    )
    return {"sessions": sessions}

@app.delete("/api/sessions/{session_id}")
async def delete_session_endpoint(
    session_id: str,
    request: Request,
    secret_key: str,
):
    return await delete_session(
        request.app.state.redis,
        session_id,
        secret_key,
    )

@app.post(
    "/api/query_agent",
    response_model=AgentRunResponse,
)
async def query_agent(
    query: QueryRequest,
    db: DbSession,
    request: Request,
    response: Response,
):
    if not query.session_id:
        raise HTTPException(
            status_code=400,
            detail="Missing session_id",
        )

    session = await get_session_context(
        request.app.state.redis,
        query.session_id,
    )
    
    await enforce_agent_rate_limits(
    request,
    query.session_id,
    response,
    )

    run = await execute_agent(
        db,
        query.schema_name,
        query.table_name,
        query.user_input,
        query.session_id,
    )

    return build_agent_run_response(
        run,
        user_id=session["user_id"],
        session_mode=session["mode"],
    )


@app.post(
    "/api/upload-csv",
    responses={
        400: {"description": "Only CSV files are supported"},
        403: {"description": "Invalid secret key"},
    },
)
async def upload_csv_file(
    db: DbSession,
    file: UploadFile = File(...),
    secret_key: str = Form(...),
    table_name: str = Form(...),
    schema_name: str = Form("public"),
):
    if secret_key != settings.UPLOAD_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid secret key")

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    return await upload_csv(
        db,
        file,
        schema_name=schema_name,
        table_name=table_name,
    )

import asyncio
import json

from fastapi import HTTPException
from fastapi.responses import StreamingResponse


def format_sse(
    event: str,
    event_id: int,
    data: dict,
) -> str:
    return (
        f"id: {event_id}\n"
        f"event: {event}\n"
        f"data: {json.dumps(data)}\n\n"
    )

async def event_stream(
    agent_task,
    queue,
    session,
):
    event_id = 0

    while True:
        if agent_task.done() and queue.empty():
            break

        try:
            event = await asyncio.wait_for(
                queue.get(),
                timeout=0.5,
            )
        except asyncio.TimeoutError:
            continue

        event_id = event["event_id"]

        yield format_sse(
            "progress",
            event_id,
            event,
        )

    try:
        run = await agent_task
        response = build_agent_run_response(
            run,
            user_id=session["user_id"],
            session_mode=session["mode"],
        )

        event_id += 1

        yield format_sse(
            "complete",
            event_id,
            response.model_dump(mode="json"),
        )

    except Exception:

        logger._logger.exception(
            "Streaming agent execution failed"
        )

        event_id += 1

        yield format_sse(
            "failed",
            event_id,
            {
                "run_id": event_id,
                "stage": "failed",
                "message": "Query could not be completed.",
            },
        )

@app.post("/api/query_agent/stream")
async def query_agent_stream(
    query: QueryRequest,
    db: DbSession,
    request: Request,
    response: Response,
):
    if not query.session_id:
        raise HTTPException(
            status_code=400,
            detail="Missing session_id",
        )

    session = await get_session_context(
    request.app.state.redis,
    query.session_id,
    )

    await enforce_agent_rate_limits(
    request,
    query.session_id,
    response,
    )

    queue = asyncio.Queue()
    event_counter = 0

    async def progress_callback(
        callback_run_id: str,
        stage: str,
        message: str,
    ):
        nonlocal event_counter

        event_counter += 1

        await queue.put(
            {
                "event_id": event_counter,
                "run_id": callback_run_id,
                "stage": stage,
                "message": message,
            }
        )

    agent_task = asyncio.create_task(
        execute_agent(
            db,
            query.schema_name,
            query.table_name,
            query.user_input,
            query.session_id,
            progress_callback=progress_callback,
        )
    )

    return StreamingResponse(
        event_stream(agent_task, queue,session),
        media_type="text/event-stream",
    )


