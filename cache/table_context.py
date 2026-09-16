import asyncio
from collections import defaultdict
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from db.fetch_context import build_table_context
from helper.logger import AppLogger

logger = AppLogger(__name__)

class TableContextCache:

    def __init__(self):
        self._cache = {}
        self._locks = {}
        logger._logger.info("Table context cache initialized")

    async def get_or_build(
        self,
        key,
        builder,
    ):

        cached = self._cache.get(key)

        if cached is not None:
            logger._logger.info("Table context cache used: %s", key)
            return cached

        lock = self._locks.setdefault(
            key,
            asyncio.Lock(),
        )

        async with lock:

            cached = self._cache.get(key)

            if cached is not None:
                logger._logger.info("Table context cache used: %s", key)
                return cached

            value = await builder()

            self._cache[key] = value

            return value

    def invalidate(
        self,
        key,
    ):
        self._cache.pop(key, None)
        logger._logger.info("Table context cache invalidated: %s", key)


table_context_cache = TableContextCache()