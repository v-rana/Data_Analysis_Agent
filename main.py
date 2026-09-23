from typing import Annotated

from fastapi import FastAPI, Depends, File, Form, HTTPException, Request, UploadFile
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
from pydantic import BaseModel

class QueryRequest(BaseModel):
    session_id: str
    schema_name: str
    table_name: str
    user_input: str


DbSession = Annotated[AsyncSession, Depends(get_session)]

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")



if settings.AUTH_ENABLED:
    app.add_middleware(
        AuthMiddleware,
        auth_service=SimpleAuthService(settings.AUTH_TOKEN),
        public_paths=["/", "/health", "/sql-agent", "/static"],
    )


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
    return {
        "ip": request.headers.get("x-real-ip")
    }

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
async def start_session(payload: SessionRequest):
    return create_session(payload.mode, payload.secret_key)


@app.get("/api/sessions")
async def get_sessions(secret_key: str):
    return list_sessions(secret_key)


@app.delete("/api/sessions/{session_id}")
async def delete_session_endpoint(session_id: str, secret_key: str):
    return delete_session(session_id, secret_key)


@app.post(
    "/api/query_agent",
    response_model=AgentRunResponse,
)
async def query_agent(query: QueryRequest, db: DbSession):
    if not query.session_id:
        raise HTTPException(
            status_code=400,
            detail="Missing session_id",
        )

    session = get_session_context(query.session_id)

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

