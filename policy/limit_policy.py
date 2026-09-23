from sqlglot import parse_one, exp
from sqlglot.expressions import Expression

from model.services_contract import PolicyResult

def ensure_limit(
    sql: str,
    *,
    limit: int = 10,
    dialect: str | None = None,
) -> PolicyResult:
    try:
        expression = parse_one(sql, dialect=dialect)

        # Handle SELECT and WITH statements
        select = None

        if isinstance(expression, exp.Select):
            select = expression
        elif isinstance(expression, exp.With):
            select = expression.this

        # If not select or If LIMIT already exists, return as-is
        if select is None or (select.args.get("limit") is not None):
            return PolicyResult(
                valid=True,
                sql=sql,
            )


        # Add LIMIT
        select.set(
            "limit",
            exp.Limit(
                expression=exp.Literal.number(limit)
            ),
        )

        return PolicyResult(
                valid=True,
                sql= expression.sql(dialect=dialect),
                warnings=["LIMIT clause added automatically"],)
    
    except Exception as exc:
        return PolicyResult(
            valid=False,
            sql=sql,
            errors=[str(exc)],
        )