"""Automatic route registration system for NCM API."""

from fastapi import FastAPI

def auto_register_routes(app: FastAPI, modules_package: str):
    """
    Automatically scan and register all functions with @ncm_api decorator.
    
    Args:
        app: FastAPI application instance
        modules_package: Package path to scan for modules
    """
    from .route_registrar import RouteRegistrar
    registrar = RouteRegistrar(app)
    return registrar.register_module_routes(modules_package)


def auto_register_services(app: FastAPI, services_package: str):
    """
    Automatically scan and register all ncm methods with @ncm_service decorator.
    
    Args:
        app: FastAPI application instance
        services_package: Package path to scan for services
    """
    from .route_registrar import RouteRegistrar
    registrar = RouteRegistrar(app)
    return registrar.register_service_routes(services_package)


def register_health_check(app: FastAPI):
    """Register basic health check endpoint."""
    from .route_registrar import RouteRegistrar
    registrar = RouteRegistrar(app)
    registrar.register_system_routes()

