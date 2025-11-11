"""
API Configuration
=================

Configuration settings for the Gemini Agent API.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings."""

    # API Configuration
    APP_NAME: str = "Gemini Agent API"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4

    # Gemini API
    GEMINI_API_KEY: str
    DEFAULT_MODEL: str = "gemini-2.0-flash-exp"
    DEFAULT_TEMPERATURE: float = 0.7
    MAX_TOKENS: Optional[int] = None

    # CORS Settings
    CORS_ORIGINS: list = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "api.log"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Database (if needed for future enhancements)
    DATABASE_URL: Optional[str] = None

    # Security
    API_KEY_ENABLED: bool = False
    API_KEYS: list = []

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()
