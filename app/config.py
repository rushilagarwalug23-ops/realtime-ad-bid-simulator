"""Configuration settings for the application."""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings class."""
    DATABASE_URL: str = 'postgresql+asyncpg://postgres:postgres@localhost:5432/adbiddb'
    REDIS_URL: str = 'redis://localhost:6379/0'
    CACHE_TTL_PUBLISHER: int = 300
    CACHE_TTL_SLOT: int = 300
    CACHE_TTL_CAMPAIGNS: int = 30
    APP_HOST: str = '0.0.0.0'
    APP_PORT: int = 8000

    class Config:
        env_file = ".env"

settings = Settings()
