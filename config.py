from pydantic_settings import BaseSettings
from pydantic import computed_field
from urllib.parse import quote_plus

class Settings(BaseSettings):
    APP_NAME: str = "sql_agent"
    
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    OPENAI_API_KEY : str
    GOOGLE_API_KEY: str
    LOG_LEVEL: str = "INFO"
    
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
    class Config:
        env_file = ".env"

settings = Settings()