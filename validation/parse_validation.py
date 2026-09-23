
from sqlglot import parse


from model.services_contract import ParseResult

def parse_sql(query: str,*,dialect:str)-> ParseResult:
    try:
        expression = parse(query, dialect=dialect)

        return ParseResult(
            success=True,
            expression=expression
        )

    except Exception as exc:
        return ParseResult(
            success=False,
            errors=[str(exc)],
        )
