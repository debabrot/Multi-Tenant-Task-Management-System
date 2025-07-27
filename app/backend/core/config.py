"""
Contains configurations
"""

# settings.py
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings for the backend service."""
    # ------------------------------------------------------------------
    # Postgres
    # ------------------------------------------------------------------
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------
    ENVIRONMENT: str = "production"
    DATABASE_URL: str

    # ------------------------------------------------------------------
    # SECURITY
    # ------------------------------------------------------------------
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int
    JWT_SECRET_KEY: str
    JWT_SCHEMES: str

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    """
    Get application settings with environment-specific configuration.

    Returns:
        Settings: Configured settings instance
    """
    return Settings()


settings = get_settings()
