from collections.abc import Awaitable, Callable
from sse.stages import ProgressStage
from helper.logger import AppLogger


logger = AppLogger(__name__)

ProgressCallback = Callable[
    [str, str, str],
    Awaitable[None],
]

async def emit_progress(
    progress_callback: ProgressCallback | None,
    run_id: str,
    stage: ProgressStage,
    message: str,
) -> None:
    if progress_callback is None:
        return

    try:
        await progress_callback(
            run_id,
            stage.value,
            message,
        )
    except Exception:
        logger._logger.warning(
            "Progress callback failed",
            exc_info=True,
        )