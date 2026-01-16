import sys
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import HTTPException
from ncm.core.logging import get_logger

logger = get_logger(__name__)



def get_vue_dist_path():
    if getattr(sys, "frozen", False):
        # onefile exe 临时解压目录
        base_dir = Path(sys._MEIPASS)
        vue_dist = base_dir / "web" / "dist"
    else:
        # 开发环境
        base_dir = Path(__file__).resolve().parent
        vue_dist = base_dir.parents[3] / "web" / "dist"
    return vue_dist


def register_vue_routes(app: FastAPI):
    """
    Register Vue SPA routes and static files.
    """
    # ---------------------
    # Vue SPA mount
    # ---------------------

    # Calculate project root from current file location:
    # .../ncm/infrastructure/http/routing/vue_router.py -> .../ncm-sync

    # PROJECT_ROOT = BASE_DIR.parents[3]  # routing -> http -> infrastructure -> ncm -> ncm-sync
    # VUE_DIST = PROJECT_ROOT / "web" / "dist"
    VUE_DIST = get_vue_dist_path()
    VUE_ASSETS = VUE_DIST / "assets"
    
    # Log paths for debugging
    # logger.debug(f"📂 Project Root: {PROJECT_ROOT}")
    logger.debug(f"📂 Vue Dist Path: {VUE_DIST}")

    if VUE_DIST.exists():
        # 1️⃣ 静态资源（Vite / Vue build）
        if VUE_ASSETS.exists():
            app.mount(
                "/assets",
                StaticFiles(directory=VUE_ASSETS),
                name="vue-assets",
            )
            logger.debug(f"✅ Mounted /assets to {VUE_ASSETS}")

        # 2️⃣ Root Path Handler
        @app.get("/", include_in_schema=False)
        async def serve_spa_root():
            """
            Serve Vue SPA index.html for root path.
            """
            index_file = VUE_DIST / "index.html"
            if index_file.exists():
                response = FileResponse(index_file)
                # Disable caching for index.html to ensure latest version is loaded
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
            return {"detail": "Vue index.html not found"}

        # 3️⃣ SPA fallback（必须在 API 后）
        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_vue_app(request: Request, full_path: str):
            """
            Serve Vue SPA index.html for non-API routes.
            """
            # Allow API routes to pass through (should be handled by previous routes, 
            # but this is a safety check if they fall through)
            if full_path.startswith(("api/", "docs", "redoc", "openapi.json", "health")):
                raise HTTPException(status_code=404, detail="Not Found")

            if full_path.startswith(("favicon-dark.svg", "favicon-light.svg", "favicon.svg")):
                favicon_file = VUE_DIST / full_path
                if favicon_file.exists():
                    return FileResponse(favicon_file)

            index_file = VUE_DIST / "index.html"
            if index_file.exists():
                response = FileResponse(index_file)
                # Disable caching for index.html
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                return response

            return {"detail": "Vue dist not found"}
    else:
        logger.warning(f"⚠️ Vue dist folder not found at {VUE_DIST}")
        
        # Fallback for when dist is missing (e.g. dev mode without build)
        @app.get("/", include_in_schema=False)
        async def root_not_found():
            return {
                "message": "Vue app not built.", 
                "instruction": "Please run 'npm run build' in 'web' directory.",
                "path_checked": str(VUE_DIST)
            }
