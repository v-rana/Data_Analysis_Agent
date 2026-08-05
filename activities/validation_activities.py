from temporalio import activity
from models import ValidationResult

@activity.defn
async def validate_sql_activity(
    sql: str,
) -> ValidationResult:
    ...