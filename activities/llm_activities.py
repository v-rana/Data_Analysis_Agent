from temporalio import activity

from agents.debugger_agent import execute_debugger_agent
from agents.sql_agent import execute_sql_agent
from models import SQLContext


@activity.defn
async def generate_sql_activity(context: SQLContext) -> str:
    return await execute_sql_agent(
        session_id=context.session_id,
        schema_name=context.schema_name,
        table_name=context.table_name,
        user_input=context.user_input,
        table_schema=context.table_schema,
    )


@activity.defn
async def repair_sql_activity(
    context: SQLContext
    ) -> str:
    return await execute_debugger_agent(
        session_id=context.session_id,
        current_query=context.current_sql ,
        error_message=context.execution_error ,
        table_schema=context.table_schema ,

    )