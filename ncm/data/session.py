"""Database session management with centralized configuration."""

from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker, Session
from .engine import get_engine
from ncm.core.constants import DATABASE_FILE_NAME
from ncm.core.path import get_config_path


class SessionManager:
    """SQLAlchemy session manager with centralized configuration."""
    
    def __init__(self, db_path: str = None):
        """Initialize session manager."""
        # 统一的数据库路径配置逻辑
        if db_path is None:
            db_path = self._get_default_db_path()
        
        self.db_path = db_path
        self.engine = get_engine(db_path)
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def _get_default_db_path(self) -> str:
        """Get default database path from config."""
        return str(get_config_path(DATABASE_FILE_NAME))
    
    @contextmanager
    def get_session(self) -> Session:
        """Get database session with automatic commit/rollback."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# Global session manager instance
_session_manager: SessionManager = None


def initialize_session_manager(db_path: str = None):
    """Initialize global session manager with specific db_path."""
    global _session_manager
    _session_manager = SessionManager(db_path)


def get_session_manager() -> SessionManager:
    """Get or create global session manager."""
    global _session_manager
    
    if _session_manager is None:
        _session_manager = SessionManager()  # 使用默认配置
    
    return _session_manager


@contextmanager
def get_session() -> Session:
    """Get database session (convenience function)."""
    manager = get_session_manager()
    with manager.get_session() as session:
        yield session


def get_current_db_path() -> str:
    """Get current database path."""
    return get_session_manager().db_path
