"""Automatic route registration system for NCM API."""

from fastapi import FastAPI
from .route_registrar import auto_register_all_routes


def auto_register_routes(app: FastAPI, modules_package: str = "ncm.client.apis"):
    """
    Automatically scan and register all functions with @ncm_api decorator.
    
    Args:
        app: FastAPI application instance
        modules_package: Package path to scan for modules (default: "ncm.modules")
    """
    from .route_registrar import RouteRegistrar
    registrar = RouteRegistrar(app)
    return registrar.register_module_routes(modules_package)


def auto_register_services(app: FastAPI, services_package: str = "ncm.api.ncm"):
    """
    Automatically scan and register all ncm methods with @ncm_service decorator.
    
    Args:
        app: FastAPI application instance
        services_package: Package path to scan for services (default: "ncm.ncm")
    """
    from .route_registrar import RouteRegistrar
    registrar = RouteRegistrar(app)
    return registrar.register_service_routes(services_package)


def register_health_check(app: FastAPI):
    """Register basic health check endpoint."""
    from .route_registrar import RouteRegistrar
    registrar = RouteRegistrar(app)
    registrar.register_system_routes()


# Backward compatibility - use the new unified function
def auto_register_all(app: FastAPI) -> dict:
    """
    Automatically register all routes (modules, services, system).
    
    Args:
        app: FastAPI application instance
        
    Returns:
        Dictionary with registration statistics
    """
    return auto_register_all_routes(app)