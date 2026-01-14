#!/usr/bin/env python3
"""
NCM Python API - Main Entry Point

网易云音乐 Python API 主程序入口
"""

import asyncio
import logging
import platform
import sys
import os
from ncm.core.logging import setup_logging

setup_logging(logging.DEBUG)

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def start_server():
    """Start the API http."""
    import uvicorn
    from ncm.infrastructure.http import create_app
    # import os as _os
    # import platform as _platform
    # import asyncio as _asyncio
    # if _platform.system() == "Windows":
    #     _asyncio.set_event_loop_policy(_asyncio.WindowsSelectorEventLoopPolicy())
    #     _os.environ.setdefault("UVICORN_RELOAD_ENGINE", "watchgod")
    
    print("启动 NCM API 服务器...")
    print("API 文档: http://localhost:8000/docs")
    print("健康检查: http://localhost:8000/health")
    print("按 Ctrl+C 停止服务器\n")
    
    uvicorn.run(
        "ncm.infrastructure.http.app:create_app",
        factory=True,
        host="0.0.0.0",
        port=8000,
        reload=False,
        use_colors=False,
        http="h11",
        # reload_dirs=["ncm"],
        # reload_excludes=["**/__pycache__/**", "**/*.pyc"],
        # reload_delay=0.5,
        log_level="debug"
    )



def main():
    """Main entry point."""
    # Fix Windows event loop policy
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Ensure default config exists
    from ncm.infrastructure.config import get_config_manager
    cfgm = get_config_manager()
    cfgm.ensure_loaded_sync()
    import os as _os
    cfg_path = cfgm.path()
    if not _os.path.exists(cfg_path):
        ok = cfgm.save_sync()
        if ok:
            print(f"已生成默认配置: {cfg_path}")
    
    # Initialize database session manager
    from ncm.infrastructure.db.session import initialize_session_manager
    from ncm.infrastructure.db.engine import close_engine
    
    initialize_session_manager()

    try:
        start_server()
    except KeyboardInterrupt:
        print("\n 程序已停止")
    finally:
        # Ensure database resources are released in the main process
        try:
            close_engine()
            print("主进程资源已释放")
        except Exception as e:
            print(f"主进程资源释放失败: {e}")


if __name__ == "__main__":
    main()
