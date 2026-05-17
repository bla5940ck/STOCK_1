"""
Pytest configuration and shared fixtures.
"""

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from src.models.database import Base


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db():
    """Create test database session"""
    # Use SQLite in-memory for tests
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def mock_settings(monkeypatch):
    """Mock settings for testing"""
    settings = {
        "LINE_CHANNEL_ACCESS_TOKEN": "test_token",
        "LINE_CHANNEL_SECRET": "test_secret",
        "SERVER_HOST": "0.0.0.0",
        "SERVER_PORT": 8000,
        "DEBUG": True,
        "LOG_LEVEL": "DEBUG",
        "DATABASE_URL": "sqlite:///test.db",
        "ALPHA_VANTAGE_API_KEY": "test_key",
        "API_TIMEOUT": 20,
        "INDEX_FETCH_TIMEOUT": 5,
        "STOCK_FETCH_TIMEOUT": 5,
        "NEWS_FETCH_TIMEOUT": 10,
        "CACHE_INDEX_TTL_MINUTES": 5,
        "CACHE_STOCK_TTL_MINUTES": 5,
        "CACHE_NEWS_TTL_HOURS": 1,
        "CACHE_TW_STOCK_TTL_HOURS": 24,
        "ENABLE_TW_STOCK_LOOKUP": True,
        "ENABLE_NEWS_TRANSLATION": False,
        "LOG_FORMAT": "json",
    }

    for key, value in settings.items():
        monkeypatch.setenv(key, str(value))

    return settings


# pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "contract: Contract tests")
    config.addinivalue_line("markers", "slow: Slow tests")
