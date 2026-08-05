import os
from langchain_openai import ChatOpenAI
from config import settings
# base_url = "https://api.openai.com/v1"
# model = "gpt-4o"

# api_key = settings.OPENAI_API_KEY
# print("api_key: ", api_key)
# llm = ChatOpenAI(
#     base_url=base_url,
#     api_key=api_key,
#     temperature=0,
#     model=model,
# )


from langchain_google_genai import ChatGoogleGenerativeAI

api_key = settings.GOOGLE_API_KEY


llm = ChatGoogleGenerativeAI(
    api_key=api_key,
    model="gemini-3.5-flash",
    temperature=0, 
    max_tokens=1500,
    timeout=None,
    max_retries=2,

)