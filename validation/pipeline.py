from models import AgentResult,QueryStatus

from validation.statement_validation import is_valid
from validation.limit_validation import ensure_limit
from helper.logger import AppLogger

logger = AppLogger(__name__)


@logger(log_result=True)
def run_pipeline(
    query: str,
    *,
    dialect: str,
) -> AgentResult:

    result = AgentResult(sql=query)

    if not is_valid(
        query,
        dialect=dialect,
    ):
        result.warnings.append(
            "Query contains disallowed statements"
        )
        result.status = QueryStatus.VALIDATION_FAILED
        return result

    safe_sql = ensure_limit(
        query,
        dialect=dialect,
    )

    if safe_sql != query:
        result.warnings.append(
            "LIMIT clause added automatically"
        )

    result.sql = safe_sql

    return result