import logging
import time
import inspect
from dataclasses import asdict, is_dataclass
from functools import wraps

from config import settings


class AppLogger:
    def __init__(self, name: str):
        self._logger = logging.getLogger(name)

    def _log_result_data(self, result):
        if not settings.LOG_RESULT_DETAILS:
            return

        try:
            if result is None:
                payload = None
            elif is_dataclass(result):
                payload = asdict(result)
            elif isinstance(result, (list, dict, tuple, set)):
                payload = result
            else:
                payload = repr(result)
        except Exception:
            payload = repr(result)

        self._logger.info("RESULT_DETAILS=%s", payload)

    def __call__(
        self,
        *,
        log_args: bool = False,
        log_result: bool = False,
    ):
        def log_input_details(args, kwargs):
            if not settings.LOG_INPUT_DETAILS:
                return

            self._logger.info("ARGS=%s KWARGS=%s", args, kwargs)

        def decorator(func):

            if inspect.iscoroutinefunction(func):

                @wraps(func)
                async def wrapper(*args, **kwargs):
                    start = time.perf_counter()

                    self._logger.info("START %s", func.__qualname__)

                    if log_args:
                        log_input_details(args, kwargs)

                    try:
                        result = await func(*args, **kwargs)

                        if log_result:
                            self._logger.info(
                                "RESULT=%s",
                                type(result).__name__,
                            )
                            self._log_result_data(result)

                        return result

                    except Exception:
                        self._logger.exception(
                            "FAILED %s",
                            func.__qualname__,
                        )
                        raise

                    finally:
                        elapsed = (
                            time.perf_counter() - start
                        ) * 1000

                        self._logger.info(
                            "END %s %.2fms",
                            func.__qualname__,
                            elapsed,
                        )

                return wrapper

            @wraps(func)
            def wrapper(*args, **kwargs):
                start = time.perf_counter()

                self._logger.info("START %s", func.__qualname__)

                if log_args:
                    log_input_details(args, kwargs)

                try:
                    result = func(*args, **kwargs)

                    if log_result:
                        self._logger.info(
                            "RESULT=%s",
                            type(result).__name__,
                        )
                        self._log_result_data(result)

                    return result

                except Exception:
                    self._logger.exception(
                        "FAILED %s",
                        func.__qualname__,
                    )
                    raise

                finally:
                    elapsed = (
                        time.perf_counter() - start
                    ) * 1000

                    self._logger.info(
                        "END %s %.2fms",
                        func.__qualname__,
                        elapsed,
                    )

            return wrapper

        return decorator