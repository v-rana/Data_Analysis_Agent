from typing import Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from models import AgentResult, QueryStatus

async def execute_sql_query(
    result: AgentResult,
    db: AsyncSession,
) -> AgentResult:

    try:
        query_result = await db.execute(
            text(result.sql)
        )

        result.rows = query_result.mappings().all()

    except Exception as exc:
        result.status = QueryStatus.EXECUTION_FAILED
        result.execution_error = str(exc)
        result.execution_error_type = type(exc).__name__
    
    return result