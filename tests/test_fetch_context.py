import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from db.fetch_context import (fetch_tables_under_schema,
                              fetch_tbl_attr,fetch_field_details)
from db.conn import get_session

@pytest.mark.asyncio
async def test_get_tables(db_conn: AsyncSession):
    schema_name = "public"

    result = await fetch_tables_under_schema(db_conn, schema_name)

    assert isinstance(result, list)
    assert all(isinstance(table, str) for table in result)
    assert "test_tbl" in result

async def test_tbl_attr():
    session = get_session()
    result = await fetch_tbl_attr(session,"public",["air_traffic_passenger_statistics_20260718"])
    print(result)

test_tbl_attr()


#test fetch field details
async def test_fetch_field_details(db_conn: AsyncSession):
    pass
