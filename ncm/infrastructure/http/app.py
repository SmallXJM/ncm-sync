"""FastAPI application factory for NCM API http."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from .routing.auto_router import auto_register_routes, auto_register_services, register_health_check
from ncm.infrastructure.db.async_session import dispose_async_engine
import asyncio


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events handler for FastAPI.
    Handles startup and shutdown logic.
    """
    try:
        # Startup logic here (if needed)
        yield
    except asyncio.CancelledError:
        # Handle cancellation gracefully
        pass
    finally:
        # Shutdown logic
        # Cleanup service instances with cleanup method
        instances = getattr(app.state, "service_instances", [])
        for inst in instances:
            try:
                cleanup = getattr(inst, "cleanup", None)
                if cleanup:
                    if callable(cleanup):
                        result = cleanup()
                        if hasattr(result, "__await__"):
                            try:
                                await result
                            except Exception:
                                pass
            except Exception:
                pass
        
        # Dispose shared async DB engine
        try:
            await dispose_async_engine()
        except Exception:
            pass


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application instance
    """
    app = FastAPI(
        title="NCM Python API Server",
        description="网易云音乐 Python API 服务器 - A Python implementation of Netease Cloud Music API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
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
    auto_register_routes(app, "ncm.api.modules")
    
    # Automatically register all ncm routes
    auto_register_services(app, "ncm.api.ncm")
    
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
    
    print("🎵 Starting NCM Python API Server...")
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
