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
from db.fetch_context import fetch_tables_under_schema

from services.execute_agent_service import execute_sql_agent
from services.csv_upload_service import upload_csv
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


@app.get("/api/get_table")
async def get_table_names(db: DbSession):
    async with db.begin():
        result = await fetch_tables_under_schema(db,"public")

    return result



@app.post("/api/query_agent")
async def query_agent(query: QueryRequest, db: DbSession):
    result = await execute_sql_agent(db, query.schema_name, 
                                     query.table_name, query.user_input,
                                       query.session_id)
    return result


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

