from pydantic import BaseModel
from typing import Any
from model.services_contract import SQLAttempt,AgentRun
from helper.format_run_context import format_attempt_error
from model.services_contract import AttemptSource,AttemptStatus,RunStatus

class AttemptTraceResponse(BaseModel):
    source: AttemptSource
    status: AttemptStatus
    sql: str
    error: str | None = None


class AgentRunResponse(BaseModel):
    run_id: str
    run_status: RunStatus
    response: str | None
    attempts: list[AttemptTraceResponse]
    user_id: str
    session_mode: str
    result_rows: list[dict[str, Any]]

def build_attempt_trace(attempt: SQLAttempt) -> AttemptTraceResponse:
    return AttemptTraceResponse(
        source=attempt.source,
        status=attempt.status,
        sql=attempt.final_sql,
        error=format_attempt_error(attempt) or None,
    )

def build_agent_run_response(
    run: AgentRun,
    *,
    user_id: str,
    session_mode: str,
) -> AgentRunResponse:

    return AgentRunResponse(
        run_id=run.run_id,
        run_status=run.final_status.value,
        response=run.final_response,
        result_rows=run.result_rows,
        attempts=[
            build_attempt_trace(a)
            for a in run.attempts
        ],
        user_id=user_id,
        session_mode=session_mode,
    )   