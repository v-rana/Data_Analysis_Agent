from models import ExecutionResult
from temporalio import activity

@activity.defn
async def execute_sql_activity(
    sql: str,
) -> ExecutionResult:
    ...