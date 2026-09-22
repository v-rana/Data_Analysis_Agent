import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from config import settings
from services.sql_runner import run_sql_attempt


async def _run(sql: str):
    engine = create_async_engine(settings.DB_URL, echo=False)
    async with async_sessionmaker(engine, expire_on_commit=False)() as db:
        return await run_sql_attempt(sql, db, dialect="postgres", source="real_db_test")


def test_valid_select_with_existing_limit():
    sql = 'SELECT * FROM public.air_traffic_passenger_statistics_20260718 LIMIT 10'
    attempt = asyncio.run(_run(sql))
    assert attempt.validation and attempt.validation.valid
    assert attempt.execution and attempt.execution.success


def test_valid_select_without_limit():
    sql = "SELECT SUM(\"Passenger Count\") FROM public.air_traffic_passenger_statistics_20260718 WHERE \"Activity Period Start Date\" >= '2024-01-01' AND \"Activity Period Start Date\" <= '2024-12-31'"
    attempt = asyncio.run(_run(sql))
    assert attempt.policy and attempt.policy.valid
    assert attempt.execution and attempt.execution.success
    assert 'LIMIT 10' in attempt.policy.sql


def test_invalid_disallowed_sql():
    attempt = asyncio.run(_run('DELETE FROM public.air_traffic_passenger_statistics_20260718'))
    assert attempt.validation and not attempt.validation.valid
    assert attempt.execution is None


def test_valid_sql_execution_failure():
    attempt = asyncio.run(_run('SELECT * FROM public.does_not_exist'))
    assert attempt.validation and attempt.validation.valid
    assert attempt.execution and not attempt.execution.success
