from services.execute_agent_service import execute_sql_agent
from db.conn import get_session
from llm.llm_obj import llm
from prompt_manager.prompt_component import get_prompt_template

import asyncio

async def test_execute_agent():
    prompt  = get_prompt_template('sql_agent_system_prompt',
                                    'sql_agent_user_template')
    chain = prompt | llm


    query = "how many passengers travelled in 2024"
    async for db in get_session():
        result = await execute_sql_agent(db,chain,"public",
                                        "air_traffic_passenger_statistics_20260718",
                                    query)
    print(result)

asyncio.run(test_execute_agent())