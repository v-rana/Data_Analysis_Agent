from enum import Enum

class ProgressStage(str, Enum):
    GENERATING = "generating"
    GENERATED = "generated"
    EXECUTING = "executing"
    REPAIRING = "repairing"
    COMPLETED = "completed"
    FAILED = "failed"