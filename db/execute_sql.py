from typing import Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from models import AgentResult, QueryStatus
from helper.logger import AppLogger

logger = AppLogger(__name__)


@logger(log_result=True)
async def execute_sql_query(
    sql: str,
    db: AsyncSession,
) -> dict:
    logger._logger.info("Executing SQL query")
    query_result = await db.execute(
        text(sql)
    )

    rows = query_result.mappings().all()

    return rows