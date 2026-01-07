#!/usr/bin/env python3
"""
NCM Python API Server Launcher

启动 NCM Python API 服务器的便捷脚本
"""

import asyncio
import platform
import sys
import os
import os as _os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main entry point for http launcher."""
    
    # Fix for Windows event loop policy
    # if platform.system() == "Windows":
    #     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    #     _os.environ.setdefault("UVICORN_RELOAD_ENGINE", "watchgod")
    
    try:
        import uvicorn
        from ncm.infrastructure.http import create_app
        
        print("🎵 NCM Python API Server")
        print("=" * 50)
        print("📖 API 文档: http://localhost:8000/docs")
        print("🔍 备用文档: http://localhost:8000/redoc") 
        print("❤️  健康检查: http://localhost:8000/health")
        print("🌐 服务器地址: http://localhost:8000")
        print("=" * 50)
        print("按 Ctrl+C 停止服务器")
        print()
        
        app = create_app()
        
        uvicorn.run(
            "ncm.infrastructure.http.app:create_app",
            factory=True,
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=["ncm"],
            reload_excludes=["**/__pycache__/**", "**/*.pyc"],
            reload_delay=0.5,
            log_level="info",
            access_log=True
        )
        
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
