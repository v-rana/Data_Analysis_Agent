# model/services_contract.py
from sqlglot.expressions import Expression

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AttemptStatus(str, Enum):
    SUCCESS = "success"
    PARSE_FAILED = "parse_failed"
    VALIDATION_FAILED = "validation_failed"
    POLICY_FAILED = "policy_failed"
    EXECUTION_FAILED = "execution_failed"
    
    @property
    def retryable(self) -> bool:
        return self in {
            AttemptStatus.PARSE_FAILED,
            AttemptStatus.EXECUTION_FAILED,
        }

class RunStatus(str, Enum):
    RUNNING = "running"
    OUT_OF_SCOPE = "out_of_scope"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY_EXHAUSTED = "retry_exhausted"

class ScopeStatus(str, Enum):
    IN_SCOPE = "in_scope"
    OUT_OF_SCOPE = "out_of_scope"

class AttemptSource(str, Enum):
    GENERATION = "generation"
    REPAIR = "repair"

@dataclass
class ScopeResult:
    status: ScopeStatus
    reason: str | None = None

@dataclass
class ParseResult:
    success: bool
    expression: list[Expression] | None = None
    errors: list[str] = field(default_factory=list)

@dataclass
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)


@dataclass
class PolicyResult:
    valid: bool
    sql: str
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class ExecutionResult:
    success: bool
    rows: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    error_type: str | None = None


@dataclass
class SQLAttempt:
    original_sql: str
    source: str = "sql_runner"
    parse: ParseResult | None = None
    validation: ValidationResult | None = None
    policy: PolicyResult | None = None
    execution: ExecutionResult | None = None

    @property
    def final_sql(self) -> str:
        if self.policy is not None:
            return self.policy.sql

        return self.original_sql

    @property
    def status(self) -> AttemptStatus:
        if self.parse is None:
            raise RuntimeError("SQLAttempt has not been parsed")

        if not self.parse.success:
            return AttemptStatus.PARSE_FAILED

        if self.validation is None:
            raise RuntimeError("SQLAttempt has not been validated")

        if not self.validation.valid:
            return AttemptStatus.VALIDATION_FAILED

        if self.policy is None:
            raise RuntimeError("SQLAttempt has not completed policy evaluation")

        if not self.policy.valid:
            return AttemptStatus.POLICY_FAILED

        if self.execution is None:
            raise RuntimeError("SQLAttempt has not been executed")

        if not self.execution.success:
            return AttemptStatus.EXECUTION_FAILED

        return AttemptStatus.SUCCESS

@dataclass
class SQLGenerationResult:
    sql: str
    model: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None

@dataclass
class AgentRun:
    run_id: str
    session_id: str
    user_input: str

    scope: ScopeResult | None = None
    attempts: list[SQLAttempt] = field(default_factory=list)

    final_status: RunStatus = RunStatus.RUNNING
    final_response: str | None = None
    result_rows: list[dict[str, Any]] = field(default_factory=list)

@dataclass
class RepairAttempt:
    attempt_number: int

    failed_sql: str

    error_type: str

    error_message: str

    repaired_sql: str | None = None

@dataclass
class RepairContext:
    user_question: str

    failed_sql: str

    error_message: str

    error_type: str

    schema_context: str

    repair_history: list[RepairAttempt]