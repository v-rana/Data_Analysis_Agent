from collections.abc import Awaitable, Callable

from helper.logger import AppLogger


logger = AppLogger(__name__)

ProgressCallback = Callable[
    [str, str],
    Awaitable[None],
]

async def emit_progress(
    progress_callback: ProgressCallback | None,
    stage: str,
    message: str,
) -> None:
    if progress_callback is None:
        return

    try:
        await progress_callback(stage, message)
    except Exception:
        logger._logger.warning(
            "Progress callback failed",
            exc_info=True,
        )