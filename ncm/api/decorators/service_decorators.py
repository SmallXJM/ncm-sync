"""Service decorators for NCM ncm layer endpoints."""

from functools import wraps
from typing import Callable, List


def ncm_service(path: str, methods: List[str] = None):
    """
    NCM Service decorator for exposing ncm layer methods as HTTP endpoints.
    
    This decorator only marks the method for route registration and preserves
    the original function behavior. The actual HTTP conversion is handled
    by the route handler in the routing layer.
    
    Args:
        path: API endpoint path (e.g., "/ncm/auth/qr-login")
        methods: HTTP methods allowed (default: ["POST"])
    
    Usage:
        @ncm_service("/ncm/auth/qr-login", ["POST"])
        async def start_qr_login(self, **kwargs) -> Dict[str, Any]:
            # ... implementation
    """
    if methods is None:
        methods = ["POST"]
    
    def decorator(func: Callable) -> Callable:
        func._ncm_service_route = {
            "path": path,
            "methods": methods,
            "original_func": func,
            "type": "http",
        }
        return func
    
    return decorator


def ncm_ws_service(path: str):
    def decorator(func: Callable) -> Callable:
        func._ncm_service_route = {
            "path": path,
            "methods": ["WS"],
            "original_func": func,
            "type": "ws",
        }
        return func
    
    return decorator
