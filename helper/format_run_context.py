from model.services_contract import SQLAttempt,AttemptStatus

def format_attempt_error(
    attempt: SQLAttempt,
) -> str:
    match attempt.status:

        case AttemptStatus.PARSE_FAILED:
            return "\n".join(
                attempt.parse.errors
                if attempt.parse
                else []
            )

        case AttemptStatus.VALIDATION_FAILED:
            return "\n".join(
                attempt.validation.errors
                if attempt.validation
                else []
            )

        case AttemptStatus.POLICY_FAILED:
            return "\n".join(
                attempt.policy.errors
                if attempt.policy
                else []
            )

        case AttemptStatus.EXECUTION_FAILED:
            if not attempt.execution:
                return ""

            return (
                f"Error Type: {attempt.execution.error_type}\n"
                f"Error: {attempt.execution.error}"
            )

        case _:
            return ""
        
def format_current_attempt(
    attempt: SQLAttempt,
) -> str:

    sql = attempt.final_sql

    error_context = format_attempt_error(
        attempt
    )

    return f"""
        Status:
        {attempt.status.value}

        SQL:
        {sql}

        Failure Details:
        {error_context}
        """.strip()

def format_attempt_history(
    attempts: list[SQLAttempt],
    *,
    max_attempts: int = 3,
) -> str:

    if not attempts:
        return "No previous attempts."

    sections: list[str] = []

    recent_attempts = attempts[-max_attempts:]

    for idx, attempt in enumerate(
        recent_attempts,
        start=1,
    ):
        sections.append(
            f"""
Attempt {idx}
Source: {attempt.source}
Status: {attempt.status.value}

SQL:
{attempt.final_sql}

Error:
{format_attempt_error(attempt)}
""".strip()
        )

    return "\n\n---\n\n".join(sections)
