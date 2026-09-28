"""Configuration settings for the application."""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings class."""
    # Defaults to SQLite for instant local execution without Docker.
    # Set to 'postgresql+asyncpg://postgres:postgres@localhost:5432/adbiddb' in .env for PostgreSQL.
    DATABASE_URL: str = 'sqlite+aiosqlite:///./adbid.db'
    REDIS_URL: str = 'redis://localhost:6379/0'
    CACHE_TTL_PUBLISHER: int = 300
    CACHE_TTL_SLOT: int = 300
    CACHE_TTL_CAMPAIGNS: int = 30
    APP_HOST: str = '0.0.0.0'
    APP_PORT: int = 8000

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
