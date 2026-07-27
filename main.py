from fastapi import FastAPI ,Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.conn import get_session
from db.fetch_context import fetch_tables_under_schema,fetch_tbl_attr,fetch_field_details

from services.execute_agent_service import execute_sql_agent

app = FastAPI()

tbl_names = ["air_traffic_passenger_statistics_20260718"]
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "app": "sql_agent",
    }

@app.get("/get_table")
async def get_table_names( db: AsyncSession = Depends(get_session) ):
    async with db.begin():
        result = await fetch_tables_under_schema(db,"public")

    return result

@app.get("/tbl_attrs")
async def test_tbl_attr(db: AsyncSession = Depends(get_session)):

    result = await fetch_tbl_attr(db,"public",["air_traffic_passenger_statistics_20260718"])
    return result

@app.get("/field_details")
async def test_get_categories(db: AsyncSession = Depends(get_session)):
    result = await fetch_field_details(db,"public","air_traffic_passenger_statistics_20260718",
                                       ["Price Category Code","Activity Type Code"])
    return result

from pydantic import BaseModel
class QueryRequest(BaseModel):
    session_id: str
    schema_name: str
    table_name: str
    user_input: str

@app.post("/query_agent")
async def query_agent(query:QueryRequest,db: AsyncSession = Depends(get_session)):

    result = await execute_sql_agent(db,query.session_id,query.schema_name,
                                     query.table_name, query.user_input)
    
    return result

