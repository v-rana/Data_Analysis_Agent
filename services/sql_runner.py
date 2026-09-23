from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from db.execute_sql import execute_sql_query
from model.services_contract import ExecutionResult, SQLAttempt
from policy.limit_policy import ensure_limit
from validation.statement_validation import is_valid
from validation.parse_validation import parse_sql

async def run_sql_attempt(
    sql: str,
    db: AsyncSession,
    *,
    dialect: str = "postgres",
    source: str = "sqlrunner",
) -> SQLAttempt:
    """Validate and execute a SQL statement using the contract-based result model."""

    attempt = SQLAttempt(
        original_sql=sql,
        source=source,
    )

    # parsing
    attempt.parse = parse_sql(sql,dialect=dialect)

    if not attempt.parse.success:
        return attempt
    
    # validation
    attempt.validation = is_valid(
        attempt.parse.expression
    )

    if not attempt.validation.valid:
        return attempt

    attempt.policy = ensure_limit(
        sql,
        dialect=dialect,
    )

    if not attempt.policy.valid:
        return attempt

    try:
        rows = await execute_sql_query(
            attempt.final_sql,
            db,
        )

        attempt.execution = ExecutionResult(
            success=True,
            rows=rows,
        )
    except Exception as exc:
        attempt.execution = ExecutionResult(
            success=False,
            rows=[],
            error=str(exc),
            error_type=type(exc).__name__,
        )
    return attempt
