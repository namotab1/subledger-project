from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, read from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "SubLedger"
    database_url: str  # required: the app refuses to start without it
    invoice_due_days: int = 14


@lru_cache
def get_settings() -> Settings:
    return Settings()