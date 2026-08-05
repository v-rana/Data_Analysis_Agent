from langchain_core.runnables.history import RunnableWithMessageHistory

from prompt_manager.prompt_component import debugger_agent_prompt_template
from llm.llm_obj import llm
from llm_memory.memory_handler import get_hybrid_session_history

from models import RepairAttempt

def build_debugger_agent(llm, prompt_name):
    prompt = debugger_agent_prompt_template(prompt_name)
    chain = prompt | llm
    return RunnableWithMessageHistory(
        chain,
        get_hybrid_session_history,
        input_messages_key="user_input",
        history_messages_key="chat_history",
    )


_AGENT = build_debugger_agent(llm, "debug_agent_sys_prompt")


async def execute_debugger_agent(
    session_id: str,
    current_query: str,
    error_message: str,
    table_schema: str,
    debug_history: list[RepairAttempt] | None = None,
) -> str:
    llm_output = await _AGENT.ainvoke(
        {
            "debug_history": debug_history,
            "current_query": current_query,
            "error_message": error_message,
            "table_schema": table_schema,
        },
        config={
            "configurable": {
                "session_id": session_id,
            }
        },
    )
    return llm_output.text


    