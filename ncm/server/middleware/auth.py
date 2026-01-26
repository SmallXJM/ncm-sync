
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse
from ncm.server.auth import AuthHandler
from ncm.core.config import get_config_manager

import logging

logger = logging.getLogger(__name__)



class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Check if auth is enabled
        conf = get_config_manager().model().auth
        logger.info(f"Auth enabled: {conf.enabled}")
        
        if not conf.enabled:
            return await call_next(request)

        path = request.url.path
        
        logger.info(f"Request path: {path}")
        
        # Public endpoints whitelist
        # Allow /login (frontend), /api/auth/login, static files, and websocket
        if (path.startswith("/api/auth/login") or 
            path == "/" or 
            path.startswith("/assets") or 
            path.startswith("/@") or  # Vite specific
            path.startswith("/src") or # Vite specific
            path.startswith("/node_modules") or # Vite specific
            path == "/favicon.ico" or
            path == "/favicon.svg" or
            path == "/login" ):
            # path.startswith("/ws")): # WebSocket might need separate auth handling
            return await call_next(request)

        # Allow OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Check Authorization header
        # Only enforce auth for API endpoints
        if path.startswith("/api") or path.startswith("/ncm") or path.startswith("/ws"):
             auth_header = request.headers.get("Authorization")
             if not auth_header or not auth_header.startswith("Bearer "):
                return JSONResponse(
                    status_code=401,
                    content={"code": 401, "message": "Not authenticated"}
                )

             # Verify token
             token = auth_header.split(" ")[1]
             payload = AuthHandler.verify_token(token)
             if not payload:
                 return JSONResponse(
                    status_code=401,
                    content={"code": 401, "message": "Invalid or expired token"}
                )
             # Store user info in state
             request.state.user = payload


        return await call_next(request)
