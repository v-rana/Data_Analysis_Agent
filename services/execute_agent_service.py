
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from db.fetch_context import  build_table_context

from helper.format_context import format_table_context

from agents.sql_agent import execute_sql_agent
from agents.debugger_agent import execute_debugger_agent

from cache.table_context import table_context_cache
from model.services_contract import (
    AgentRun,
    AttemptSource,
    AttemptStatus,
    RunStatus,
    ScopeResult,
    ScopeStatus,
)

from helper.logger import AppLogger
from services.sql_runner import run_sql_attempt

MAX_RETRIES = 2
logger = AppLogger(__name__)



@logger(log_result=True)
async def execute_agent(
    db: AsyncSession,
    schema_name: str,
    tbl_name: str,
    user_input: str,
    session_id: str,
) -> AgentRun:
    run = AgentRun(
        run_id=str(uuid4()),
        session_id=session_id,
        user_input=user_input,
    )

    try:
        run.scope = ScopeResult(
            status=ScopeStatus.IN_SCOPE,
        )
        if run.scope.status == ScopeStatus.OUT_OF_SCOPE:
            run.final_status = RunStatus.OUT_OF_SCOPE
            run.final_response = run.scope.reason
            return run

        
        table_context = await table_context_cache.get_or_build(
            key=(schema_name, tbl_name),
            builder=lambda: build_table_context(
                db,
                schema_name,
                tbl_name,
            ),
        )


        additional_context = format_table_context(
            table_context
        )

        sql_query = await execute_sql_agent(
            session_id=session_id,
            schema_name=schema_name,
            table_name=tbl_name,
            user_input=user_input,
            additional_context=additional_context,
        )

        print("-" * 30)
        print("RETURNED SQL QUERY:", sql_query)
        print("-" * 30)

        attempt = await run_sql_attempt(
            sql_query,
            db,
            dialect="postgres",
            source=AttemptSource.GENERATION,
        )

        run.attempts.append(attempt)

        if attempt.status == AttemptStatus.SUCCESS:
            run.final_status = RunStatus.SUCCESS
            run.result_rows = attempt.execution.rows
            return run
        
        if not attempt.status.retryable:
            run.final_status = RunStatus.FAILED
            return run



        for retry in range(MAX_RETRIES):

            print(f"CURRENT RETRY: {retry} LEVEL")

            repaired_sql = await execute_debugger_agent(
                session_id=session_id,
                current_attempt=attempt,
                attempt_history=run.attempts,
                table_schema=additional_context,
            )


            print(
                f"PREVIOUS SQL: "
                f"{attempt.final_sql or attempt.original_sql}\n"
                f"NEW SQL: {repaired_sql}"
            )

            repaired_attempt = await run_sql_attempt(
                repaired_sql,
                db,
                dialect="postgres",
                source=AttemptSource.REPAIR,
            )

            run.attempts.append(repaired_attempt)

            if repaired_attempt.status == AttemptStatus.SUCCESS:
                run.final_status = RunStatus.SUCCESS
                run.result_rows = repaired_attempt.execution.rows
                return run

            if not repaired_attempt.status.retryable:
                run.final_status = RunStatus.FAILED
                return run
            
            attempt = repaired_attempt

        run.final_status = RunStatus.RETRY_EXHAUSTED
        return run
    except Exception as exc:
        logger._logger.exception(
            f"UNHANDLED FAILURE: {exc}"
        )
        raise
