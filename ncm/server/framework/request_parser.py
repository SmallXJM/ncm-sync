"""Request parameter parsing utilities."""

from typing import Dict, Any
from fastapi import Request


async def parse_request_params(request: Request) -> Dict[str, Any]:
    """Parse request parameters from different sources."""
    params = {}
    
    # Get query parameters (for GET requests)
    if request.query_params:
        params.update(dict(request.query_params))
    
    # Get JSON body (for POST requests)
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            content_type = request.headers.get("content-type", "").lower()
            # Try to parse as JSON if content-type is json or empty (fallback)
            if "application/json" in content_type or not content_type:
                try:
                    json_data = await request.json()
                    if isinstance(json_data, dict):
                        params.update(json_data)
                except Exception:
                    # Ignore JSON parse errors if content type is empty
                    if "application/json" in content_type:
                        raise
            elif "application/x-www-form-urlencoded" in content_type:
                form_data = await request.form()
                params.update(dict(form_data))
        except Exception:
            # If parsing fails, continue with empty params
            pass
    
    # Add cookies as a parameter
    if request.cookies:
        cookie_str = "; ".join([f"{k}={v}" for k, v in request.cookies.items()])
        params['cookie'] = cookie_str
    
    # Process NCM-specific configuration parameters
    # These parameters are used by RequestOptions and should be handled specially
    ncm_config_params = {
        'proxy', 'user_agent', 'real_ip', 'random_cn_ip', 'device_id',
        'crypto', 'encrypt_response', 'check_token', 'timeout', 'os_type'
    }
    
    # Convert string values to appropriate types for NCM config params
    for key, value in params.items():
        if key in ncm_config_params and isinstance(value, str):
            # Handle boolean conversions
            if key in ['random_cn_ip', 'encrypt_response', 'check_token']:
                if value.lower() in ('true', '1', 'yes', 'on'):
                    params[key] = True
                elif value.lower() in ('false', '0', 'no', 'off'):
                    params[key] = False
            
            # Handle integer conversions
            elif key in ['timeout']:
                try:
                    params[key] = int(value)
                except ValueError:
                    pass  # Keep as string if conversion fails
            
            # Handle crypto type conversion
            elif key == 'crypto':
                from ...core.options import CryptoType
                crypto_map = {
                    'weapi': CryptoType.WEAPI,
                    'eapi': CryptoType.EAPI,
                    'linuxapi': CryptoType.LINUXAPI,
                    'api': CryptoType.API
                }
                if value.lower() in crypto_map:
                    params[key] = crypto_map[value.lower()]
            
            # Handle os_type conversion
            elif key == 'os_type':
                from ...core.options import OSType
                os_map = {
                    'pc': OSType.PC,
                    'linux': OSType.LINUX,
                    'android': OSType.ANDROID,
                    'iphone': OSType.IPHONE
                }
                if value.lower() in os_map:
                    params[key] = os_map[value.lower()]
    
    return params