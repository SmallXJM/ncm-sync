#!/usr/bin/env python3
"""
NCM Sync - Main Entry Point.

支持命令行参数：
  --host  服务监听地址，默认 0.0.0.0
  --port  服务监听端口，默认 17666
  --debug 启用调试模式（等价于原 debug.py 行为）
"""

import asyncio
import platform
import sys
import os
import logging
import argparse
import re
from pathlib import Path
from ncm.core.logging import setup_logging, get_logger
from ncm.core.path import get_app_base

logger = get_logger(__name__)

HOST_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]+$")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="NCM Sync - 音乐同步工具")
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="服务监听主机地址，默认 0.0.0.0",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=17666,
        help="服务监听端口号，默认 17666",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="启用调试模式",
    )

    args = parser.parse_args(argv)

    if not 1 <= args.port <= 65535:
        parser.error("参数 --port 必须在 1-65535 范围内")

    if not args.host or " " in args.host or not HOST_PATTERN.match(args.host):
        parser.error("参数 --host 必须是有效的 IP 地址或域名格式")

    return args

def setup_environment():
    """Prepare system environment."""
    # Add current directory to Python path
    sys.path.insert(0, str(get_app_base()))

    # Fix Windows event loop policy
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def ensure_config():
    """Ensure default configuration exists."""
    from ncm.core.config import get_config_manager

    cfgm = get_config_manager()
    cfgm.ensure_loaded_sync()
    cfg_path = cfgm.path()

    if not Path(cfg_path).exists():
        ok = cfgm.save_sync()
        if ok:
            logger.info("已生成默认配置: %s", cfg_path)


def init_database():
    """Initialize database session and engine."""
    from ncm.data.session import initialize_session_manager
    initialize_session_manager()


def close_database():
    """Close database engine."""
    from ncm.data.engine import close_engine
    try:
        close_engine()
        logger.info("主进程资源已释放")
    except Exception as e:
        logger.error("主进程资源释放失败: %s", e)


def start_server(host: str, port: int, debug: bool):
    """Start the API server via uvicorn."""
    import uvicorn

    uvicorn.run(
        "ncm.server.app:create_app",
        factory=True,
        host=host,
        port=port,
        reload=debug,
        use_colors=False,
        http="h11",
        log_config=None,
        timeout_graceful_shutdown=5 if debug else None,
    )


def main(argv=None):
    """Main entry point."""
    args = parse_args(argv)
    setup_environment()
    log_level = logging.DEBUG if args.debug else logging.INFO
    os.environ["NCM_LOG_LEVEL"] = str(log_level)
    setup_logging(log_level)
    ensure_config()
    init_database()

    try:
        start_server(args.host, args.port, args.debug)
    except KeyboardInterrupt:
        logger.info("程序已停止")
    finally:
        close_database()


if __name__ == "__main__":
    main()
