from typing import Any
from dataclasses import dataclass, field
from models import QueryStatus

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