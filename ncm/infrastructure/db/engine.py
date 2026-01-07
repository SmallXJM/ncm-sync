"""Database engine configuration and management."""

import os
from sqlalchemy import create_engine, Engine, text
from sqlalchemy.ext.declarative import declarative_base

# SQLAlchemy Base for all models
Base = declarative_base()

# Global engine instance
_engine: Engine = None


def create_engine_instance(db_path: str = "ncm_data.db") -> Engine:
    """Create SQLAlchemy engine instance."""
    # Ensure database directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    # Create engine with SQLite
    engine = create_engine(
        f"sqlite:///{db_path}",
        echo=False,  # Set to True for SQL debugging
        pool_pre_ping=True,
        connect_args={"check_same_thread": False}
    )
    
    with engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL;"))
        conn.execute(text("PRAGMA synchronous=NORMAL;"))
        conn.execute(text("PRAGMA busy_timeout=5000;"))
        conn.commit()
    
    return engine


def get_engine(db_path: str = "ncm_data.db") -> Engine:
    """Get or create global engine instance."""
    global _engine
    
    if _engine is None:
        _engine = create_engine_instance(db_path)
        # Create all tables
        Base.metadata.create_all(bind=_engine)
        # Create recommended indexes
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
