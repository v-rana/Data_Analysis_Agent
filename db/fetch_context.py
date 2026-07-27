from typing import Any
from sqlalchemy import (inspect,MetaData, Table, func,select)
from sqlalchemy.ext.asyncio import (
    AsyncSession,)
from sqlalchemy.sql.sqltypes import String


async def fetch_tables_under_schema(db_conn: AsyncSession,schema: str) -> list[str]:
    #using the inspect function to get the table names directly
    conn = await db_conn.connection()

    def _get_tables(sync_conn):
        inspector = inspect(sync_conn)
        return inspector.get_table_names(schema=schema)
    async with conn.begin():
        return await conn.run_sync(_get_tables)


async def fetch_tbl_attr(db_conn: AsyncSession ,schema_name:str,
                         tbl_names: list[str]) -> dict[dict]:
    conn = await db_conn.connection()
    def _get_table_attrs(sync_conn):
        inspector = inspect(sync_conn)

        result = {}

        for table in tbl_names:
            columns = inspector.get_columns(
                table_name=table,
                schema=schema_name,
            )

            pk = inspector.get_pk_constraint(
                table_name=table,
                schema=schema_name,
            )

            result[table] = {
                "columns": [
                    {
                        "name": col["name"],
                        "type": str(col["type"]),
                        "nullable": col["nullable"],
                    }
                    for col in columns
                ],
                "primary_keys": pk.get("constrained_columns", []),
            }

        return result

    return await conn.run_sync(_get_table_attrs)


MAX_DISTINCT_VALUES = 30

SAMPLE_SIZE = 10


async def _load_table(
    db_conn: AsyncSession,
    schema_name: str,
    tbl_name: str,
) -> Table:
    metadata = MetaData()

    def _reflect_table(sync_conn):
        return Table(
            tbl_name,
            metadata,
            schema=schema_name,
            autoload_with=sync_conn,
        )

    conn = await db_conn.connection()
    return await conn.run_sync(_reflect_table)


async def _fetch_field_summary(
    db_conn: AsyncSession,
    table: Table,
    field_name: str,
) -> dict[str, Any]:

    col = table.c[field_name]

    distinct_count = await db_conn.scalar(
        select(func.count(col.distinct()))
    )

    if distinct_count <= MAX_DISTINCT_VALUES:
        rows = await db_conn.execute(
            select(col).distinct()
        )

        return {
            "distinct_count": distinct_count,
            "values": [row[0] for row in rows.fetchall()],
        }

    rows = await db_conn.execute(
        select(col)
        .distinct()
        .limit(SAMPLE_SIZE)
    )

    return {
        "distinct_count": distinct_count,
        "sample_values": [row[0] for row in rows.fetchall()],
    }


async def fetch_field_details(
    db_conn: AsyncSession,
    schema_name: str,
    tbl_name: str,
    field_names: list[str],
) -> dict[str, dict[str, Any]]:

    table = await _load_table(
        db_conn,
        schema_name,
        tbl_name,
    )

    result: dict[str, dict[str, Any]] = {}

    for field in field_names:
        if field not in table.c:
            continue

        result[field] = await _fetch_field_summary(
            db_conn,
            table,
            field,
        )

    return result


async def build_table_context(
    db_conn: AsyncSession,
    schema_name: str,
    tbl_name: str,
) -> dict[str, Any]:

    metadata = MetaData()

    def _load_table(sync_conn):
        return Table(
            tbl_name,
            metadata,
            schema=schema_name,
            autoload_with=sync_conn,
        )

    conn = await db_conn.connection()
    table = await conn.run_sync(_load_table)

    context: dict[str, Any] = {
        "table_name": tbl_name,
        "columns": {},
    }

    for col in table.columns:

        col_info: dict[str, Any] = {
            "type": str(col.type),
            "nullable": col.nullable,
        }

        if not isinstance(col.type, String):
            continue

        rows = await db_conn.execute(
            select(col)
            .where(col.is_not(None))
            .distinct()
            .limit(MAX_DISTINCT_VALUES)
        )

        values = [row[0] for row in rows.fetchall()]

        if values:
            col_info["values"] = values

        context["columns"][col.name] = col_info

    return context