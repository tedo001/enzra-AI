"""Async database engine & session management.

Wraps SQLAlchemy's async engine. Uses an in-memory SQLite fallback when no
PostgreSQL is configured/reachable, so the API and tests run standalone.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings, get_settings
from app.database.models import Base
from app.logging_config import get_logger

log = get_logger(__name__)


class Database:
    def __init__(self, url: str) -> None:
        self._url = url
        self._engine = create_async_engine(url, future=True, pool_pre_ping=True)
        self._sessionmaker = async_sessionmaker(self._engine, expire_on_commit=False)

    async def create_all(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        log.info("database schema ready", url=self._safe_url)

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self._sessionmaker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def dispose(self) -> None:
        await self._engine.dispose()

    @property
    def _safe_url(self) -> str:
        # Never log credentials.
        return self._url.split("@")[-1]


_DB_SINGLETON: Database | None = None


def get_database(settings: Settings | None = None) -> Database:
    """Return the process-wide :class:`Database` singleton (lazily built).

    ``Settings`` is a mutable pydantic model and therefore unhashable, so we
    cache the instance manually rather than via ``lru_cache``.
    """
    global _DB_SINGLETON
    if _DB_SINGLETON is not None:
        return _DB_SINGLETON

    settings = settings or get_settings()
    url = settings.database_url
    try:
        _DB_SINGLETON = Database(url)
    except Exception as exc:  # pragma: no cover - driver/config dependent
        log.warning("primary DB unavailable, using in-memory sqlite", error=str(exc))
        _DB_SINGLETON = Database("sqlite+aiosqlite:///:memory:")
    return _DB_SINGLETON
