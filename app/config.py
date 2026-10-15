from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings read from the environment (LIBRARY_API_KEY, DATABASE_URL)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    library_api_key: str | None = None
    database_url: str = "sqlite:///./library.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()
