
import logging
import json
from urllib.parse import parse_qs
from starlette.types import ASGIApp, Scope, Receive, Send
from ncm.server.auth import AuthHandler
from ncm.core.config import get_config_manager
from starlette.middleware.base import BaseHTTPMiddleware
logger = logging.getLogger(__name__)


class AuthMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        # Check if auth is enabled
        conf = get_config_manager().model().auth
        
        if not conf.enabled:
            await self.app(scope, receive, send)
            return

        path = scope["path"]
        
        # Public endpoints whitelist
        # Allow /login (frontend), /api/auth/login, /api/auth/config, static files, and websocket
        if (path.startswith("/api/auth/login") or 
            path.startswith("/api/auth/config") or 
            path == "/" or 
            path.startswith("/assets") or 
            path.startswith("/@") or  # Vite specific
            path.startswith("/src") or # Vite specific
            path.startswith("/node_modules") or # Vite specific
            path == "/favicon.ico" or
            path == "/favicon.svg" or
            path == "/login" ):
            await self.app(scope, receive, send)
            return

        # Allow OPTIONS requests (CORS preflight) for HTTP
        if scope["type"] == "http" and scope["method"] == "OPTIONS":
            await self.app(scope, receive, send)
            return

        # Only enforce auth for API endpoints and WebSocket
        if not (path.startswith("/api") or path.startswith("/ncm") or path.startswith("/ws") or path.startswith("/local")):
             await self.app(scope, receive, send)
             return

        token = None
        
        # 1. HTTP Auth (Bearer Header)
        if scope["type"] == "http":
            headers = dict(scope["headers"])
            # Headers are lowercased in ASGI
            auth_header = headers.get(b"authorization", b"").decode()
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        # 2. WebSocket Auth (Query Param)
        elif scope["type"] == "websocket":
            query_string = scope.get("query_string", b"").decode()
            qs = parse_qs(query_string)
            token_list = qs.get("token")
            if token_list:
                token = token_list[0]

        # Verify token
        if token:
            payload = AuthHandler.verify_token(token)
            if payload:
                # Success
                # Store user info in state (compatible with request.state.user)
                scope.setdefault("state", {})
                scope["state"]["user"] = payload
                await self.app(scope, receive, send)
                return

        # Failure handling
        logger.warning(f"Authentication failed for {scope['type']} request to {path}")
        
        if scope["type"] == "http":
            response_body = json.dumps({"code": 401, "message": "Not authenticated or invalid token"}).encode()
            await send({
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    (b"content-type", b"application/json"),
                ],
            })
            await send({
                "type": "http.response.body",
                "body": response_body,
            })
        elif scope["type"] == "websocket":
            # Close connection with policy violation code
            await send({"type": "websocket.close", "code": 1008})
