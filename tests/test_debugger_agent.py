import pytest

from agents import debugger_agent


class DummyLLMResponse:
    def __init__(self, text: str):
        self.text = text


@pytest.mark.asyncio
async def test_execute_debugger_agent_returns_fixed_sql(monkeypatch):
    session_id = "test-session"
    current_query = "SELECT * FROM air_traffic_passenger_statistics_20260718 WHERE pass_year = 2024"
    error_message = "column \"pass_year\" does not exist"
    table_schema = '"Year" INTEGER, "Passengers" INTEGER'
    expected_sql = (
        'SELECT * FROM air_traffic_passenger_statistics_20260718 '
        'WHERE "Year" = 2024'
    )

    async def fake_ainvoke(params, config=None):
        assert params["debug_history"] == ""
        assert params["current_query"] == current_query
        assert params["error_message"] == error_message
        assert params["table_schema"] == table_schema
        assert config is not None
        assert config["configurable"]["session_id"] == session_id
        return DummyLLMResponse(expected_sql)

    monkeypatch.setattr(debugger_agent._AGENT, "ainvoke", fake_ainvoke)

    result = await debugger_agent.execute_debugger_agent(
        session_id=session_id,
        current_query=current_query,
        error_message=error_message,
        table_schema=table_schema,
    )

    assert result == expected_sql
