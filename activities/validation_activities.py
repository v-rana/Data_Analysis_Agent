from temporalio import activity
from model.services_contract import ValidationResult

@activity.defn
async def validate_sql_activity(
    sql: str,
) -> ValidationResult:
    ...