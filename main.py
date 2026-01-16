#!/usr/bin/env python3
"""
NCM Python API - Main Entry Point
"""

import asyncio
import platform
import sys
import os
import logging
from ncm.core.logging import setup_logging, get_logger

logger = get_logger(__name__)
log_level = logging.INFO
os.environ["NCM_LOG_LEVEL"] = str(log_level)  # 字符串形式

def setup_environment():
    """Prepare system environment."""
    # Add current directory to Python path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    # Fix Windows event loop policy
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def ensure_config():
    """Ensure default configuration exists."""
    from ncm.infrastructure.config import get_config_manager

    cfgm = get_config_manager()
    cfgm.ensure_loaded_sync()
    cfg_path = cfgm.path()
    import os

    if not os.path.exists(cfg_path):
        ok = cfgm.save_sync()
        if ok:
            logger.info("已生成默认配置: %s", cfg_path)


def init_database():
    """Initialize database session and engine."""
    from ncm.infrastructure.db.session import initialize_session_manager
    initialize_session_manager()


def close_database():
    """Close database engine."""
    from ncm.infrastructure.db.engine import close_engine
    try:
        close_engine()
        logger.info("主进程资源已释放")
    except Exception as e:
        logger.error("主进程资源释放失败: %s", e)


def start_server():
    """Start the API server via uvicorn."""
    import uvicorn

    uvicorn.run(
        "ncm.infrastructure.http.app:create_app",
        factory=True,
        host="0.0.0.0",
        port=8000,
        reload=False,  # 开发环境可改 True
        use_colors=False,
        http="h11",
        log_config=None,
    )


def main():
    """Main entry point."""
    setup_environment()
    setup_logging(log_level)
    ensure_config()
    init_database()

    try:
        start_server()
    except KeyboardInterrupt:
        logger.info("程序已停止")
    finally:
        close_database()


if __name__ == "__main__":
    main()
