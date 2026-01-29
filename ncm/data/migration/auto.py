"""Automatic database migration runner."""

import os
import logging
from pathlib import Path
from typing import Optional

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, text, inspect
from ncm.core.path import get_app_base

logger = logging.getLogger(__name__)

def _get_alembic_config(db_url: str) -> Config:
    """
    Construct Alembic configuration object.
    
    Args:
        db_url: Database connection URL
        
    Returns:
        Alembic Config object
    """
    # In dev: ncm/data/alembic.ini
    # In frozen: We need to make sure we can find it.
    # Assuming standard structure:
    # project_root/ncm/data/alembic.ini
    
    # Note: get_app_base returns project root
    project_root = get_app_base()
    
    # Try to find alembic.ini in possible locations
    # 1. ncm/data/alembic.ini (Source/Dev)
    # 2. _internal/ncm/data/alembic.ini (PyInstaller)
    
    # We use a robust search strategy
    possible_paths = [
        project_root / "ncm" / "data" / "alembic.ini",
        project_root / "_internal" / "ncm" / "data" / "alembic.ini",
    ]
    
    # Also check relative to this file
    current_dir = Path(__file__).resolve().parent # ncm/data/migration
    data_dir = current_dir.parent # ncm/data
    possible_paths.insert(0, data_dir / "alembic.ini")
    
    alembic_ini_path = None
    for p in possible_paths:
        if p.exists():
            alembic_ini_path = p
            break
            
    if not alembic_ini_path:
        raise FileNotFoundError("Could not find alembic.ini")
        
    logger.debug(f"Using alembic.ini at: {alembic_ini_path}")
    
    # Create Config object
    alembic_cfg = Config(str(alembic_ini_path))
    
    # Override script_location to be absolute
    # In alembic.ini it is usually "migration", relative to alembic.ini
    # We make it absolute to avoid CWD issues
    script_location = data_dir / "migration"
    alembic_cfg.set_main_option("script_location", str(script_location))
    
    # Set database URL dynamically
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    
    return alembic_cfg


def run_migrations(engine: Engine, db_url: str):
    """
    Run database migrations automatically.
    
    Handles both fresh installs and upgrades from non-Alembic databases.
    
    Args:
        engine: SQLAlchemy Engine instance
        db_url: Database connection URL
    """
    logger.debug("Checking database schema status...")
    
    try:
        # Create Alembic config
        alembic_cfg = _get_alembic_config(db_url)
        
        # Check current DB state
        with engine.connect() as connection:
            inspector = inspect(connection)
            tables = inspector.get_table_names()
            
            has_alembic_version = "alembic_version" in tables
            has_data_tables = "account_sessions" in tables # Check for a key table
            
            if has_alembic_version:
                # Normal case: Alembic is managing this DB
                logger.debug("Found version table. Running upgrades...")
                command.upgrade(alembic_cfg, "head")
                
            elif has_data_tables:
                # Legacy case: Tables exist but no alembic_version
                # This implies an existing DB from before migrations were added.
                # We assume the schema matches the 'head' state at the time of migration introduction.
                logger.warning("Found existing tables without version tracking. Stamping as head...")
                
                # Mark database as up-to-date without running migrations
                command.stamp(alembic_cfg, "head")
                
                # Run upgrade just in case (should be no-op if head matches)
                command.upgrade(alembic_cfg, "head")
                
            else:
                # Fresh install: No tables
                logger.debug("No tables found. Initializing database schema...")
                command.upgrade(alembic_cfg, "head")
                
        logger.debug("Database schema is up to date.")
        
    except Exception as e:
        logger.error(f"Automatic migration failed: {str(e)}")
        # We re-raise to prevent app from starting with bad DB
        raise
