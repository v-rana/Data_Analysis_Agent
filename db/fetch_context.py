from typing import Any

from sqlalchemy import (
    MetaData,
    Table,
    inspect,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.sqltypes import String
from helper.logger import AppLogger

logger = AppLogger(__name__)

MAX_DISTINCT_VALUES = 30


async def fetch_schemas(db_conn: AsyncSession) -> list[str]:
    logger._logger.info("Listing schemas")
    conn = await db_conn.connection()

    def _get_schemas(sync_conn):
        inspector = inspect(sync_conn)
        schemas = inspector.get_schema_names()
        return [
            schema for schema in schemas
            if schema not in {"information_schema", "pg_catalog"}
            and not schema.startswith("pg_")
        ]

    return await conn.run_sync(_get_schemas)


async def fetch_tables_under_schema(db_conn: AsyncSession,schema: str) -> list[str]:
    logger._logger.info("Listing tables for schema: %s", schema)
    #using the inspect function to get the table names directly
    conn = await db_conn.connection()

    def _get_tables(sync_conn):
        inspector = inspect(sync_conn)
        return inspector.get_table_names(schema=schema)
    return await conn.run_sync(_get_tables)

async def load_table(
    db: AsyncSession,
    schema_name: str,
    table_name: str,
) -> tuple[Table, set[str]]:
    logger._logger.info("Reflecting table: %s.%s", schema_name, table_name)

    metadata = MetaData()

    def _load(sync_conn):
        table = Table(
            table_name,
            metadata,
            schema=schema_name,
            autoload_with=sync_conn,
        )

        inspector = inspect(sync_conn)

        pk = inspector.get_pk_constraint(
            table_name=table_name,
            schema=schema_name,
        )

        return (
            table,
            set(pk.get("constrained_columns", [])),
        )

    conn = await db.connection()

    result = await conn.run_sync(_load)
    logger._logger.info("Reflected table: %s.%s", schema_name, table_name)
    return result


async def get_column_values(
    db: AsyncSession,
    column,
) -> list[Any]:
    logger._logger.info("Loading distinct values for column: %s", column.name)

    rows = await db.execute(
        select(column)
        .where(column.is_not(None))
        .distinct()
        .limit(MAX_DISTINCT_VALUES + 1)
    )

    values = [
        row[0]
        for row in rows.fetchall()
        if row[0] is not None
    ]

    if len(values) > MAX_DISTINCT_VALUES:
        return []

    logger._logger.info("Loaded %d distinct values for column: %s", len(values), column.name)
    return values


async def build_table_context(
    db: AsyncSession,
    schema_name: str,
    table_name: str,
) -> dict[str, Any]:
    logger._logger.info("Building table context: %s.%s", schema_name, table_name)

    table, primary_keys = await load_table(
        db,
        schema_name,
        table_name,
    )

    context = {
        "schema_name": schema_name,
        "table_name": table_name,
        "columns": {},
    }

    for column in table.columns:

        column_info = {
            "type": str(column.type),
            "nullable": column.nullable,
            "is_primary_key": column.name in primary_keys,
        }

        if isinstance(column.type, String):

            values = await get_column_values(
                db,
                column,
            )

            if values:
                column_info["values"] = values

        context["columns"][column.name] = column_info

    logger._logger.info("Built table context: %s.%s", schema_name, table_name)
    return context