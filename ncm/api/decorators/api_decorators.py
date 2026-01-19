"""API decorators for NCM module endpoints."""

from typing import Callable, List


def ncm_api(path: str, methods: List[str] = None):
    """
    NCM API decorator that marks functions for automatic route registration.
    
    This decorator only saves route information and preserves the original
    function behavior. The actual HTTP conversion is handled by the route
    handler in the routing layer.
    
    Args:
        path: API endpoint path (e.g., "/api/login/status")
        methods: HTTP methods allowed (default: ["POST"])
    
    Usage:
        @ncm_api("/api/login/status", ["GET", "POST"])
        async def login_status(**kwargs) -> APIResponse:
            # ... implementation
    """
    if methods is None:
        methods = ["POST"]
    
    def decorator(func: Callable) -> Callable:
        # Save route information to function attributes
        func._ncm_route = {
            "path": path,
            "methods": methods,
            "original_func": func
        }
        
        # Return the original function unchanged
        # HTTP conversion will be handled by create_module_handler
        return func
    
    return decorator