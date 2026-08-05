from typing import Any
from dataclasses import dataclass, field
from enum import Enum


class QueryStatus(str, Enum):
    VALIDATION_FAILED = "validation_failed"
    EXECUTION_FAILED = "execution_failed"
    SUCCESS = "success"

@dataclass
class AgentResult:
    sql: str

    status: QueryStatus = QueryStatus.SUCCESS

    rows: list[dict[str, Any]] = field(default_factory=list)

    validation_errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    execution_error: str | None = None
    execution_error_type: str | None = None

#Activities input

@dataclass
class RepairAttempt:
    sql: str
    error: str

@dataclass
class SQLContext:
    session_id: str

    schema_name: str
    table_name: str

    user_input: str

    current_sql: str | None = None

    status: QueryStatus = QueryStatus.SUCCESS

    retry_count: int = 0

    rows: list[dict[str, Any]] = field(default_factory=list)

    validation_errors: list[str] = field(default_factory=list)

    execution_error: str | None = None
    execution_error_type: str | None = None
    repair_history: list[RepairAttempt] = field(default_factory=list)




#Activities result

@dataclass
class ValidationResult:
    valid: bool
    sql: str
    errors: list[str]

@dataclass
class ExecutionResult:
    success: bool

    rows: list[dict[str, Any]] = field(default_factory=list)

    error: str | None = None
    error_type: str | None = None