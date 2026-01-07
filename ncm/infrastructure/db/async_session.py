from __future__ import annotations

from typing import AsyncIterator, Callable, Optional
import os
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

_ENGINE: Optional[AsyncEngine] = None
_SESSION_FACTORY: Optional[async_sessionmaker[AsyncSession]] = None

class UnitOfWork:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory
        self.session: Optional[AsyncSession] = None

    async def __aenter__(self):
        self.session = self._session_factory()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        try:
            if exc_type is None:
                await self.session.commit()
            else:
                await self.session.rollback()
        finally:
            await self.session.close()

def _ensure_session_factory(url: str) -> async_sessionmaker[AsyncSession]:
    global _ENGINE, _SESSION_FACTORY
    if _SESSION_FACTORY is None or _ENGINE is None:
        _ENGINE = create_async_engine(
            url,
            future=True,
            pool_pre_ping=True,
            connect_args={"timeout": 30}
        )
        async def _init_pragmas():
            async with _ENGINE.begin() as conn:
                await conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
                await conn.exec_driver_sql("PRAGMA synchronous=NORMAL;")
                await conn.exec_driver_sql("PRAGMA busy_timeout=5000;")
        import asyncio as _asyncio
        try:
            loop = _asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(_init_pragmas())
            else:
                loop.run_until_complete(_init_pragmas())
        except Exception:
            pass
        _SESSION_FACTORY = async_sessionmaker(_ENGINE, expire_on_commit=False)
    return _SESSION_FACTORY

def make_uow_factory(session_factory: async_sessionmaker[AsyncSession]) -> Callable[[], UnitOfWork]:
    def _factory() -> UnitOfWork:
        return UnitOfWork(session_factory)
    return _factory

# Unified DB URL management via environment variable
_DEFAULT_DB_URL = os.getenv("NCM_DB_URL", "sqlite+aiosqlite:///ncm_data.db")

def get_uow_factory(db_url: Optional[str] = None) -> Callable[[], UnitOfWork]:
    """
    Get a UnitOfWork factory using a unified DB URL.
    Priority: explicit db_url > env NCM_DB_URL > default sqlite+aiosqlite.
    """
    url = db_url or _DEFAULT_DB_URL
    session_factory = _ensure_session_factory(url)
    return make_uow_factory(session_factory)

async def dispose_async_engine() -> None:
    global _ENGINE, _SESSION_FACTORY
    if _ENGINE is not None:
        await _ENGINE.dispose()
    _ENGINE = None
    _SESSION_FACTORY = None
