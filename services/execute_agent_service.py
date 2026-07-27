
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.runnables.history import RunnableWithMessageHistory


from db.fetch_context import fetch_tbl_attr, build_table_context
from helper.format_context import format_table_context

from prompt_manager.prompt_component import get_prompt_template
from llm.llm_obj import llm
from llm_memory.memory_handler import get_hybrid_session_history

def _build_sql_chain():
    prompt  = get_prompt_template('sql_agent_system_prompt',
                                  'sql_agent_user_template')
    chain = prompt | llm
    sql_chain = RunnableWithMessageHistory(
        chain,
        get_hybrid_session_history,
        input_messages_key="user_input",
        history_messages_key="chat_history",
    )
    return sql_chain

async def execute_sql_agent(
    db: AsyncSession,
    session_id:str,
    schema_name: str,
    tbl_name: str,
    user_input: str,
) -> list[dict[str, Any]]:

    table_schema = await fetch_tbl_attr(
        db,
        schema_name,
        [tbl_name],
    )
    raw_json_context = await build_table_context(db,schema_name,tbl_name)
    additional_context = format_table_context(raw_json_context)
    print("-"*30)
    print(additional_context)
    print("-"*30)

    chain = _build_sql_chain()

    params = {
        "schema_name": schema_name,
        "table_name": tbl_name,
        "user_input": user_input,
        "table_schema": table_schema,
        "additional_context":additional_context,
    }
    config={
            "configurable": {
                "session_id": session_id,
            }
        }
    llm_output = await chain.ainvoke(params,config=config)
    sql_query = llm_output.text
    print("-"*30)
    print("RETURNED SQL QUERY:", sql_query)
    print("-"*30)
    result = await db.execute(text(sql_query))

    return result.mappings().all()
