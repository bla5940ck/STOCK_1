"""
Database initialization and connection management.
"""

import json
from typing import AsyncGenerator, Optional
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import (
    AsyncSession, create_async_engine, async_sessionmaker
)
from sqlalchemy.pool import NullPool, QueuePool

from src.config import get_settings
from src.models.database import Base
from src.exceptions import DatabaseError


class DatabaseManager:
    """Manage database connections and sessions"""

    def __init__(self):
        self.engine = None
        self.async_engine = None
        self.SessionLocal = None
        self.AsyncSessionLocal = None

    async def initialize(self) -> None:
        """Initialize async database engine and session factory"""
        try:
            settings = get_settings()
            db_url = settings.DATABASE_URL

            # Convert sqlite:// to sqlite+aiosqlite:// for async
            if db_url.startswith("sqlite://"):
                db_url = db_url.replace("sqlite://", "sqlite+aiosqlite:///")

            self.async_engine = create_async_engine(
                db_url,
                echo=settings.DEBUG,
                future=True,
                pool_pre_ping=True,
                poolclass=NullPool if "sqlite" in db_url else QueuePool,
            )

            self.AsyncSessionLocal = async_sessionmaker(
                self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )

            # Create tables
            async with self.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

        except Exception as e:
            raise DatabaseError(f"Failed to initialize database: {str(e)}")

    async def close(self) -> None:
        """Close database connection"""
        if self.async_engine:
            await self.async_engine.dispose()

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session"""
        if not self.AsyncSessionLocal:
            raise DatabaseError("Database not initialized")

        async with self.AsyncSessionLocal() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Database session error: {str(e)}")
            finally:
                await session.close()


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


async def init_db() -> None:
    """Initialize database on startup"""
    global _db_manager
    _db_manager = DatabaseManager()
    await _db_manager.initialize()


async def close_db() -> None:
    """Close database on shutdown"""
    global _db_manager
    if _db_manager:
        await _db_manager.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session in FastAPI endpoints"""
    global _db_manager
    if not _db_manager:
        raise DatabaseError("Database not initialized")
    async for session in _db_manager.get_session():
        yield session


def init_db_sync() -> None:
    """Synchronous database initialization (for CLI commands)"""
    settings = get_settings()
    db_url = settings.DATABASE_URL

    # Create sync engine for init
    if db_url.startswith("sqlite://"):
        engine = create_engine(db_url)
    elif db_url.startswith("postgresql://"):
        # Convert to psycopg2 driver if needed
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://")
        engine = create_engine(db_url)
    else:
        engine = create_engine(db_url)

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")
    engine.dispose()
