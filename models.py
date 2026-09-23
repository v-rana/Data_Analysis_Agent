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


@dataclass
class RepairAttempt:
    attempt_number: int
    failed_sql: str
    error_type: str
    error_message: str
    repaired_sql: str | None = None


