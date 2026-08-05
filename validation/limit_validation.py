from sqlglot import parse_one, exp
from sqlglot.expressions import Expression



def ensure_limit(
    sql: str,
    *,
    limit: int = 10,
    dialect: str | None = None,
) -> str:
    try:
        expression = parse_one(sql, dialect=dialect)
    except Exception:
        raise ValueError("Invalid SQL query")

    # Handle SELECT and WITH statements
    select = None

    if isinstance(expression, exp.Select):
        select = expression
    elif isinstance(expression, exp.With):
        select = expression.this

    if select is None:
        # Non-select statements are returned unchanged
        return sql

    # If LIMIT already exists, return as-is
    if select.args.get("limit") is not None:
        return expression.sql(dialect=dialect)

    # Add LIMIT
    select.set(
        "limit",
        exp.Limit(
            expression=exp.Literal.number(limit)
        ),
    )

    return expression.sql(dialect=dialect)