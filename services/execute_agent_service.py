
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from db.fetch_context import fetch_tbl_attr, build_table_context

from models import (AgentResult, QueryStatus, RepairAttempt)

from helper.format_context import format_table_context

from agents.sql_agent import execute_sql_agent as generate_sql_query
from agents.debugger_agent import execute_debugger_agent
from validation.pipeline import run_pipeline

from db.execute_sql import execute_sql_query
from helper.logger import AppLogger

MAX_RETRIES = 2
logger = AppLogger(__name__)


@logger(log_result=True)
async def execute_sql_agent(
    db: AsyncSession,
    schema_name: str,
    tbl_name: str,
    user_input: str,
    session_id: str,
) -> AgentResult:

    table_schema = await fetch_tbl_attr(
        db,
        schema_name,
        [tbl_name],
    )
    raw_json_context = await build_table_context(db, schema_name, tbl_name)
    additional_context = format_table_context(raw_json_context)

    sql_query = await generate_sql_query(
        session_id=session_id,
        schema_name=schema_name,
        table_name=tbl_name,
        user_input=user_input,
        table_schema=table_schema,
        additional_context=additional_context,
    )

    print("-" * 30)
    print("RETURNED SQL QUERY:", sql_query)
    print("-" * 30)

    result = run_pipeline(sql_query, dialect="postgres")

    if result.status == QueryStatus.VALIDATION_FAILED:
        return result

    result = await execute_sql_query(result, db)
    cur_retry = 0
    debug_history = []

    while result.status == QueryStatus.EXECUTION_FAILED and cur_retry < MAX_RETRIES:
        print(f"CURRENT RETRY: {cur_retry} LEVEL")
        repaired_sql = await execute_debugger_agent(
            session_id,
            result.sql,
            f"{result.execution_error_type}:{result.execution_error}",
            table_schema,
            debug_history,
        )

        print(f"PREVIOUS SQL: {result.sql}\nNEW SQL:{repaired_sql}")

        repaired_result = run_pipeline(repaired_sql, dialect="postgres")

        if repaired_result.status == QueryStatus.VALIDATION_FAILED:
            return repaired_result

        repaired_result.rows = await execute_sql_query(repaired_result.sql, db)
        result = repaired_result
        debug_history.append(RepairAttempt(sql=result.sql, error=result.execution_error or ""))
        cur_retry += 1

    return result
