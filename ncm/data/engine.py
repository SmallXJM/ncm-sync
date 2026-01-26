"""Database engine configuration and management."""

from typing import Optional
from sqlalchemy import create_engine, Engine, text
from ncm.core.path import prepare_path, get_config_path
from ncm.core.constants import DATABASE_FILE_NAME
from ncm.data.models.base import Base
from ncm.data.migration.auto import run_migrations

# Global engine instance
_engine: Optional[Engine] = None


def create_engine_instance(db_path: str = None) -> Engine:
    """Create SQLAlchemy engine instance."""
    if db_path is None:
        db_path = str(get_config_path(DATABASE_FILE_NAME))

    # Ensure database directory exists
    prepare_path(db_path)
    
    db_url = f"sqlite:///{db_path}"
    
    # Create engine with SQLite
    engine = create_engine(
        db_url,
        echo=False,  # Set to True for SQL debugging
        pool_pre_ping=True,
        connect_args={"check_same_thread": False}
    )
    
    with engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL;"))
        conn.execute(text("PRAGMA synchronous=NORMAL;"))
        conn.execute(text("PRAGMA busy_timeout=5000;"))
        conn.commit()
    
    return engine, db_url


def get_engine(db_path: str = None) -> Engine:
    """Get or create global engine instance."""
    global _engine
    
    if _engine is None:
        _engine, db_url = create_engine_instance(db_path)
        
        # Run automatic migrations
        # This replaces Base.metadata.create_all(bind=_engine)
        run_migrations(_engine, db_url)
        
        # Create recommended indexes (optional, can be moved to migration scripts later)
        _create_indexes(_engine)
    
    return _engine


def _create_indexes(engine: Engine):
    """Create recommended indexes for performance."""
    with engine.connect() as conn:
        # Critical index for current session selection
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_sessions_valid_selected 
            ON account_sessions (is_valid, last_selected_at)
        """))
        
        # Index for account-session relationship
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_sessions_account 
            ON account_sessions (account_id)
        """))
        
        conn.commit()


def close_engine():
    """Close global engine instance."""
    global _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None
