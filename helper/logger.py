import logging
import time
import inspect
from functools import wraps


class AppLogger:
    def __init__(self, name: str):
        self._logger = logging.getLogger(name)

    def __call__(
        self,
        *,
        log_args: bool = False,
        log_result: bool = False,
    ):
        def decorator(func):

            if inspect.iscoroutinefunction(func):

                @wraps(func)
                async def wrapper(*args, **kwargs):
                    start = time.perf_counter()

                    self._logger.info("START %s", func.__qualname__)

                    if log_args:
                        self._logger.info(
                            "ARGS=%s KWARGS=%s",
                            args,
                            kwargs,
                        )

                    try:
                        result = await func(*args, **kwargs)

                        if log_result:
                            self._logger.info(
                                "RESULT=%s",
                                type(result).__name__,
                            )

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
                    self._logger.info(
                        "ARGS=%s KWARGS=%s",
                        args,
                        kwargs,
                    )

                try:
                    result = func(*args, **kwargs)

                    if log_result:
                        self._logger.info(
                            "RESULT=%s",
                            type(result).__name__,
                        )

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