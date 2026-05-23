"""
Application configuration loading from environment variables.
"""

import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # LINE Messaging API
    LINE_CHANNEL_ACCESS_TOKEN: str = "placeholder"
    LINE_CHANNEL_SECRET: str = "placeholder"

    # Server
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = int(os.environ.get("PORT", "8000"))  # Railway sets PORT env var
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "sqlite:///./app.db"

    # External APIs
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    TWELVE_DATA_API_KEY: Optional[str] = None
    FINNHUB_API_KEY: Optional[str] = None

    # Timeouts (seconds) - Standardized per spec requirement
    # All timeouts are configured to meet <2s total query response time
    # Reference: plan.md Technical Context & spec.md Performance Goals
    API_TIMEOUT: int = 20  # Generic API timeout (fallback, for Alpha Vantage)
    INDEX_FETCH_TIMEOUT: int = 5  # Yahoo Finance index queries (primary)
    STOCK_FETCH_TIMEOUT: int = 5  # Yahoo Finance stock queries (primary)
    NEWS_FETCH_TIMEOUT: int = 10  # Google News RSS feeds
    
    # Individual API client timeouts (should align with above):
    # - yahoo_finance.py: 15s (sync requests via requests lib) → SHOULD USE INDEX/STOCK_FETCH_TIMEOUT
    # - alpha_vantage.py: 20s (fallback for stocks/indices)
    # - google_news.py: 10s (RSS feeds)
    # - tw_fundamentals.py: 10s
    # - tw_rating_scraper.py: 15s
    # - twelve_data_client.py: 8s
    # - finnhub_client.py: 8s

    # Cache TTLs
    CACHE_INDEX_TTL_MINUTES: int = 5
    CACHE_STOCK_TTL_MINUTES: int = 5
    CACHE_NEWS_TTL_HOURS: int = 1
    CACHE_TW_STOCK_TTL_HOURS: int = 24

    # Feature Flags
    ENABLE_TW_STOCK_LOOKUP: bool = True
    ENABLE_NEWS_TRANSLATION: bool = False

    # Logging
    LOG_FORMAT: str = "json"
    LOG_FILE: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

    def validate_required(self) -> None:
        """Validate that all required environment variables are set"""
        required_fields = [
            "LINE_CHANNEL_ACCESS_TOKEN",
            "LINE_CHANNEL_SECRET",
        ]

        missing_fields = []
        for field in required_fields:
            if not getattr(self, field, None):
                missing_fields.append(field)

        if missing_fields:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_fields)}"
            )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    settings = Settings()
    settings.validate_required()
    return settings
