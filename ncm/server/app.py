"""FastAPI application factory for NCM API http."""

from contextlib import asynccontextmanager
import threading
import logging
import os
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from .framework.auto_router import (
    auto_register_routes,
    auto_register_services,
    register_health_check,
)
from .framework.vue_router import register_vue_routes
from .framework.local_music_router import register_local_music_routes
from ncm.data.async_session import dispose_async_engine
from ncm.data.engine import close_engine
from ncm.client.protocol.session import close_session
from ncm.core.logging import get_logger, setup_logging
from ncm.core.constants import PACKAGE_CLIENT_APIS, PACKAGE_SERVER_ROUTERS

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events handler for FastAPI.
    Handles startup and shutdown logic.
    """
    logger.info("Application startup: initializing resources...")
    try:
        # Startup logic here (if needed)
        yield
    except asyncio.CancelledError:
        # Handle cancellation gracefully
        logger.info("Application shutdown requested (Cancelled)...")
    finally:
        logger.info("Application shutdown: cleaning up resources...")
        
        # Cleanup service instances with cleanup method
        instances = getattr(app.state, "service_instances", [])
        for inst in instances:
            try:
                cleanup = getattr(inst, "cleanup", None)
                if cleanup and callable(cleanup):
                    logger.debug(f"Cleaning up service: {inst.__class__.__name__}")
                    result = cleanup()
                    if hasattr(result, "__await__"):
                        try:
                            await result
                        except Exception as e:
                            logger.warning(f"Async cleanup failed for {inst.__class__.__name__}: {e}")
            except Exception as e:
                logger.error(f"Error during service cleanup: {e}")
        
        # Dispose shared async DB engine
        try:
            logger.debug("Disposing async database engine...")
            await dispose_async_engine()
        except Exception as e:
            logger.error(f"Failed to dispose async engine: {e}")

        # Dispose global HTTP session
        try:
            logger.debug("Closing global HTTP session...")
            await close_session()
        except Exception as e:
            logger.error(f"Failed to close global HTTP session: {e}")

        # Dispose sync DB engine (if initialized)
        try:
            logger.debug("Disposing sync database engine...")
            close_engine()
        except Exception as e:
            logger.error(f"Failed to dispose sync engine: {e}")

        # Final cleanup: Cancel pending tasks and shutdown executor
        try:
            # 1. Log active threads for diagnosis
            for t in threading.enumerate():
                if t is not threading.current_thread():
                    logger.debug(f"Active thread at shutdown: {t.name} (daemon={t.daemon})")

            # 2. Cancel all pending tasks
            current_task = asyncio.current_task()
            tasks = [t for t in asyncio.all_tasks() if t is not current_task]
            if tasks:
                logger.info(f"Cancelling {len(tasks)} pending async tasks...")
                for task in tasks:
                    task.cancel()
                
                # Wait briefly for tasks to acknowledge cancellation, suppressing CancelledError
                try:
                    await asyncio.gather(*tasks, return_exceptions=True)
                except asyncio.CancelledError:
                    # If we are cancelled while waiting, we can't do much more
                    logger.debug("Gathering pending tasks was cancelled")

            # 3. Shutdown default executor if it exists
            loop = asyncio.get_running_loop()
            if hasattr(loop, "_default_executor") and loop._default_executor:
                executor = loop._default_executor
                if isinstance(executor, ThreadPoolExecutor):
                    logger.info("Shutting down default ThreadPoolExecutor...")
                    # wait=False ensures we don't block if threads are stuck
                    executor.shutdown(wait=False)
                    
        except asyncio.CancelledError:
            # Swallow CancelledError during final cleanup to ensure graceful exit
            logger.info("Final cleanup interrupted by cancellation")
        except Exception as e:
            logger.error(f"Error during final cleanup: {e}")
            
        logger.info("Application shutdown complete.")


def create_app(log_level: int = None) -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application instance
    """
    # 从环境变量读取 log_level
    log_level = int(os.environ.get("NCM_LOG_LEVEL", logging.INFO))
    setup_logging(log_level)


    app = FastAPI(
        title="NCM Sync Server",
        description="NCM Sync - A Python implementation of Netease Cloud Music Sync Service",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        # docs_url="/docs",
        # redoc_url="/redoc",
        # openapi_url="/openapi.json",
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify exact origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add GZip compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Register health check endpoints
    register_health_check(app)
    
    # Automatically register all NCM API routes
    auto_register_routes(app, PACKAGE_CLIENT_APIS)
    
    # Automatically register all ncm routes
    auto_register_services(app, PACKAGE_SERVER_ROUTERS)
    
    # Local music file routes (no NCM external requests)
    register_local_music_routes(app)
    
    # Vue SPA mount
    register_vue_routes(app)


    return app


# For direct execution
if __name__ == "__main__":
    import uvicorn
    import platform
    import asyncio
    
    # Fix for Windows event loop policy
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    app = create_app()
    
    print("🎵 Starting NCM Sync Server...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔍 Alternative Docs: http://localhost:8000/redoc")
    print("❤️  Health Check: http://localhost:8000/health")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
