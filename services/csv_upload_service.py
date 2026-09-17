from io import BytesIO
from typing import Any

import pandas as pd
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from cache.table_context import table_context_cache
from helper.logger import AppLogger

logger = AppLogger(__name__)


DATE_COLUMNS = [
    "Activity Period Start Date",
    "data_as_of",
    "data_loaded_at",
]
PASSENGER_COUNT_COLUMN = "Passenger Count"


def normalize_table_name(table_name: str) -> str:
    return table_name.strip().lower()


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    for column in DATE_COLUMNS:
        if column in df.columns:
            df[column] = pd.to_datetime(df[column], errors="coerce")

    if PASSENGER_COUNT_COLUMN in df.columns:
        df["Passenger Count"] = (
            df[PASSENGER_COUNT_COLUMN]
            .astype(str)
            .str.replace(",", "", regex=False)
        )
        df[PASSENGER_COUNT_COLUMN] = pd.to_numeric(
            df[PASSENGER_COUNT_COLUMN],
            errors="coerce",
        )

    return df


async def upload_csv(
    db: AsyncSession,
    file: UploadFile,
    *,
    schema_name: str,
    table_name: str,
) -> dict[str, Any]:
    normalized_table_name = normalize_table_name(table_name)
    logger._logger.info("Starting CSV upload: %s.%s", schema_name, normalized_table_name)
    df = clean_dataframe(pd.read_csv(BytesIO(await file.read())))
    logger._logger.info("CSV parsed: %d rows, %d columns", len(df), len(df.columns))

    connection = await db.connection()
    logger._logger.info("Writing CSV data: %s.%s", schema_name, table_name)
    await connection.run_sync(
        lambda sync_connection: df.to_sql(
            name=normalized_table_name,
            con=sync_connection,
            schema=schema_name,
            if_exists="replace",
            index=False,
        )
    )

    table_context_cache.invalidate((schema_name, normalized_table_name))
    logger._logger.info("CSV upload completed: %s.%s", schema_name, normalized_table_name)
    return {
        "schema_name": schema_name,
        "table_name": normalized_table_name,
        "columns": len(df.columns),
        "rows": len(df),
    }