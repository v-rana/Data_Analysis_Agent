from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from collections.abc import AsyncGenerator
from config import settings
from helper.logger import AppLogger

logger = AppLogger(__name__)

engine = create_async_engine(
    settings.DB_URL,
    pool_size=5,
    max_overflow=0,
    echo=False,
)
logger._logger.info("Database engine initialized")

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    logger._logger.info("Opening database session")
    async with SessionLocal() as session:
        yield session

