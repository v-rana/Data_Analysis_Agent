from langchain_core.runnables.history import RunnableWithMessageHistory

from prompt_manager.prompt_component import sql_agent_prompt_template
from llm.llm_obj import llm
from llm_memory.memory_handler import get_hybrid_session_history
from helper.logger import AppLogger



logger = AppLogger(__name__)

@logger()
def build_sql_agent(llm, system_prompt_name: str, user_prompt_name: str):
    prompt = sql_agent_prompt_template(system_prompt_name, user_prompt_name)
    chain = prompt | llm
    sql_agent = RunnableWithMessageHistory(
        chain,
        get_hybrid_session_history,
        input_messages_key="user_input",
        history_messages_key="chat_history",
    )
    return sql_agent


_AGENT = build_sql_agent(llm, 'sql_agent_system_prompt', 'sql_agent_user_template')


async def execute_sql_agent(
    session_id: str,
    schema_name: str,
    table_name: str,
    user_input: str,
    table_schema: str = "",
    additional_context: str = "",
) -> str:
    params = {
        "schema_name": schema_name,
        "table_name": table_name,
        "user_input": user_input,
        "table_schema": table_schema,
        "additional_context": additional_context,
    }
    config = {
        "configurable": {
            "session_id": session_id,
        }
    }
    llm_output = await _AGENT.ainvoke(params, config=config)
    return llm_output.text
