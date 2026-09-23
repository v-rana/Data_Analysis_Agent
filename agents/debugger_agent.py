from langchain_core.runnables.history import RunnableWithMessageHistory

from prompt_manager.prompt_component import debugger_agent_prompt_template
from llm.llm_obj import llm
from llm_memory.memory_handler import get_hybrid_session_history
from helper.logger import AppLogger

from model.services_contract import SQLAttempt,AttemptStatus
from helper.format_run_context import format_current_attempt, format_attempt_history

logger = AppLogger(__name__)

@logger()
def build_debugger_agent(llm, prompt_name):
    prompt = debugger_agent_prompt_template(prompt_name)
    chain = prompt | llm
    return chain


_AGENT = build_debugger_agent(llm, "debug_agent_sys_prompt")


def build_debugger_context(
    current_attempt: SQLAttempt,
    attempt_history: list[SQLAttempt],
) -> dict[str, str]:

    return {
        "current_attempt": format_current_attempt(
            current_attempt
        ),
        "attempt_history": format_attempt_history(
            attempt_history
        ),
    }

@logger(log_result=True)
async def execute_debugger_agent(
    *,
    session_id: str,
    current_attempt: SQLAttempt,
    attempt_history: list[SQLAttempt],
    table_schema: str,
) -> str:

    prompt_context = build_debugger_context(
        current_attempt=current_attempt,
        attempt_history=attempt_history,
    )

    llm_output = await _AGENT.ainvoke(
        {
            "attempt_history": prompt_context[
                "attempt_history"
            ],
            "current_attempt": prompt_context[
                "current_attempt"
            ],
            "table_schema": table_schema,
        },
        config={
            "configurable": {
                "session_id": session_id,
            }
        },
    )

    return llm_output.text


    