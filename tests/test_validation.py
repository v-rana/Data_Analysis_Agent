from validation.limit_validation import ensure_limit
from validation.statement_validation import is_valid


def test_ensure_limit_adds_limit_to_select_query():
    result = ensure_limit("SELECT * FROM users", dialect="postgres")
    assert "LIMIT 10" in result


def test_ensure_limit_preserves_existing_limit():
    result = ensure_limit("SELECT * FROM users LIMIT 5", dialect="postgres")
    assert "LIMIT 5" in result
    assert "LIMIT 10" not in result


def test_is_valid_accepts_read_only_select_query():
    assert is_valid("SELECT * FROM users", dialect="postgres") is True


def test_is_valid_rejects_write_statement():
    assert is_valid("DELETE FROM users", dialect="postgres") is False


def test_is_valid_accepts_with_cte_query():
    query = '''WITH yearly_totals AS (
        SELECT
            EXTRACT(YEAR FROM "Activity Period Start Date") AS "Year",
            SUM("Passengers") AS total_passengers
        FROM air_traffic_passenger_statistics_20260718
        GROUP BY 1
    )
    SELECT * FROM yearly_totals'''
    assert is_valid(query, dialect="postgres") is True


def test_is_valid_rejects_invalid_sql_string():
    assert is_valid("not valid sql", dialect="postgres") is False
