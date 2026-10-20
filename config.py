import logging

from pydantic_settings import BaseSettings
from pydantic import computed_field, field_validator
from typing import Literal
from urllib.parse import quote_plus

logging.basicConfig(level=logging.INFO)

class Settings(BaseSettings):
    APP_NAME: str = "sql_agent"

    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    REDIS_SESSION_TTL: int = 7
    REDIS_SESSION_TTL_UNIT: Literal[
        "seconds","minutes","hours","days",] = "days"
    SESSION_CREATE_RATE_LIMIT: int = 3
    SESSION_CREATE_RATE_WINDOW_SECONDS: int = 3600

    AGENT_SESSION_RATE_LIMIT_PER_MINUTE: int = 3
    AGENT_SESSION_RATE_LIMIT_PER_DAY: int = 10
    AGENT_IP_RATE_LIMIT_PER_HOUR: int = 10
    AGENT_SESSION_RATE_WINDOW_SECONDS: int = 60
    AGENT_SESSION_DAY_WINDOW_SECONDS: int = 86400
    AGENT_IP_RATE_WINDOW_SECONDS: int = 3600
    
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    OPENAI_API_KEY: str
    GOOGLE_API_KEY: str
    # Optional: required only when DEEPSEEK_API_KEY or LLM_PROVIDER=deepseek.
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # Selectable LLM used outside agents (e.g. conversation summarization).
    LLM_PROVIDER: Literal["google", "openai", "deepseek"] = "google"
    LLM_MODEL: str = ""
    LLM_TEMPERATURE: float = 0
    LLM_MAX_TOKENS: int = 1500
    LLM_MAX_RETRIES: int = 2

    # Agents are pinned to this provider/model and ignore LLM_PROVIDER.
    AGENT_LLM_PROVIDER: Literal["google", "openai", "deepseek"] = "google"
    AGENT_LLM_MODEL: str = "gemini-3.5-flash"

    AUTH_ENABLED: bool = False
    AUTH_TOKEN: str = "change-me"
    UPLOAD_SECRET_KEY: str

    LOG_LEVEL: str = "INFO"
    LOG_RESULT_DETAILS: bool = False
    LOG_INPUT_DETAILS: bool = False
    
    @field_validator("LLM_PROVIDER", "AGENT_LLM_PROVIDER", mode="before")
    @classmethod
    def _normalize_provider(cls, value: str) -> str:
        return str(value).strip().lower()

    @computed_field
    @property
    def DB_URL(self) -> str:
        password = quote_plus(self.POSTGRES_PASSWORD)
        return (
            f"postgresql+asyncpg://"
            f"{self.POSTGRES_USER}:"
            f"{password}@"
            f"{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
        )
    @computed_field
    @property
    def REDIS_SESSION_TTL_SECONDS(self) -> int:
        multipliers = {
            "seconds": 1,
            "minutes": 60,
            "hours": 3600,
            "days": 86400,
        }
        return self.REDIS_SESSION_TTL * multipliers[
            self.REDIS_SESSION_TTL_UNIT
        ]
    class Config:
        env_file = ".env"

settings = Settings()