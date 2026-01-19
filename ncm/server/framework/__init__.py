"""Routing package for NCM http."""

from .auto_router import auto_register_routes, auto_register_services, register_health_check
from .route_registrar import RouteRegistrar
from .route_handlers import create_module_handler, create_service_handler
from .request_parser import parse_request_params
from .module_scanner import ModuleScanner, ServiceScanner

__all__ = [
    # Legacy auto router functions (backward compatibility)
    "auto_register_routes",
    "auto_register_services", 
    "register_health_check",
    
    # New modular components
    "RouteRegistrar",
    "create_module_handler",
    "create_service_handler",
    "parse_request_params",
    "ModuleScanner",
    "ServiceScanner"
]