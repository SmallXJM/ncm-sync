"""Route handler creation utilities."""

import inspect
from typing import Callable
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from .request_parser import parse_request_params
from ncm.client import APIResponse
from ncm.client.exceptions import NCMError, APIError, AuthenticationError, RateLimitError, NetworkError, ValidationError
from ncm.core.logging import get_logger

logger = get_logger(__name__)


def _convert_api_response_to_json(result: APIResponse) -> JSONResponse:
    """Convert APIResponse to FastAPI JSONResponse with proper header filtering."""
    
    # Filter headers - only keep safe and useful ones
    safe_headers = {}
    if result.headers:
        # Headers that should be blocked (can cause browser issues)
        blocked_headers = {
            'content-encoding', 'content-length', 'transfer-encoding',
            'connection', 'keep-alive', 'proxy-connection',
            'http', 'date', 'expires', 'cache-control',
            'cdn-ip', 'cdn-source', 'cdn-user-ip', 'via',
            'x-cv', 'x-dsa-origin-status', 'x-dsa-trace-id',
            'x-request-ip', 'x-traceid', 'x-traceid-v2',
            'x-tt-trace-tag', 'x-via', 'gw-thread', 'gw-time',
            'mconfig-bucket', 'http-timing', 'vary'
        }
        
        # Headers that are useful to keep
        allowed_headers = {
            'set-cookie', 'x-custom-', 'x-ncm-', 'x-music-',
            'access-control-', 'content-type'
        }
        
        for key, value in result.headers.items():
            key_lower = key.lower()
            
            # Skip blocked headers
            if key_lower in blocked_headers:
                continue
                
            # Keep explicitly allowed headers
            keep_header = False
            for allowed_prefix in allowed_headers:
                if key_lower.startswith(allowed_prefix):
                    keep_header = True
                    break
            
            if keep_header:
                safe_headers[key] = value
    
    # Convert APIResponse to FastAPI Response
    response = JSONResponse(
        content=result.body,
        status_code=result.status,
        headers=safe_headers
    )
    
    # Handle cookies
    for cookie in result.cookies:
        if '=' in cookie:
            parts = cookie.split('=', 1)
            if len(parts) == 2:
                name, value = parts
                # Parse additional cookie attributes if needed
                cookie_parts = value.split(';')
                cookie_value = cookie_parts[0].strip()
                response.set_cookie(name.strip(), cookie_value)
    
    return response


def create_module_handler(func: Callable) -> Callable:
    """Create a FastAPI route handler from an NCM API module function."""
    
    async def handler(request: Request):
        try:
            # Parse request parameters
            params = await parse_request_params(request)
            
            # Call the original function with parsed parameters
            result: APIResponse = await func(**params)
            
            # Convert APIResponse to JSONResponse for FastAPI
            return _convert_api_response_to_json(result)
            
        except AuthenticationError as e:
            logger.exception("AuthenticationError")
            raise HTTPException(status_code=401, detail={"code": e.code, "message": e.message})
        except RateLimitError as e:
            logger.exception("RateLimitError")
            raise HTTPException(status_code=429, detail={"code": e.code, "message": e.message})
        except APIError as e:
            logger.exception("APIError")
            raise HTTPException(status_code=400, detail={"code": e.code, "message": e.message})
        except NetworkError as e:
            logger.exception("NetworkError")
            raise HTTPException(status_code=503, detail={"code": 503, "message": f"Network error: {str(e)}"})
        except NCMError as e:
            logger.exception("NCMError")
            raise HTTPException(status_code=500, detail={"code": 500, "message": str(e)})
        except Exception as e:
            logger.exception("Unhandled exception occurred")
            raise HTTPException(status_code=500, detail={"code": 500, "message": f"Internal http error: {str(e)}"})
    
    return handler


def create_service_handler(service_method: Callable) -> Callable:
    """Create a FastAPI route handler from a ncm method."""
    
    async def handler(request: Request):
        try:
            # Parse request parameters
            params = await parse_request_params(request)
            
            # Call the ncm method with parsed parameters
            if inspect.iscoroutinefunction(service_method):
                result = await service_method(**params)
            else:
                result = service_method(**params)
            
            # Service methods now return APIResponse objects
            if isinstance(result, APIResponse):
                # Convert APIResponse to JSONResponse for FastAPI
                return _convert_api_response_to_json(result)
            
            # Fallback for legacy Dict[str, Any] returns (should not happen after refactor)
            if not isinstance(result, dict):
                result = {"data": result}
            
            # Ensure success field exists for legacy responses
            if "success" not in result:
                result["success"] = True
            
            # Return JSON response for legacy format
            status_code = 200 if result.get("success", True) else 400
            return JSONResponse(
                content=result,
                status_code=status_code
            )
            
        except ValidationError as e:
            logger.exception("ValidationError")
            raise HTTPException(status_code=400, detail={"code": 400, "message": str(e)})
        except AuthenticationError as e:
            logger.exception("AuthenticationError")
            raise HTTPException(status_code=401, detail={"code": 401, "message": e.message})
        except RateLimitError as e:
            logger.exception("RateLimitError")
            raise HTTPException(status_code=429, detail={"code": 429, "message": e.message})
        except APIError as e:
            logger.exception("APIError")
            raise HTTPException(status_code=400, detail={"code": 400, "message": e.message})
        except NetworkError as e:
            logger.exception("NetworkError")
            raise HTTPException(status_code=503, detail={"code": 503, "message": f"Network error: {str(e)}"})
        except NCMError as e:
            logger.exception("NCMError")
            raise HTTPException(status_code=500, detail={"code": 500, "message": str(e)})
        except Exception as e:
            logger.exception("Unhandled exception occurred")
            raise HTTPException(status_code=500, detail={"code": 500, "message": f"Internal http error: {str(e)}"})
    
    return handler