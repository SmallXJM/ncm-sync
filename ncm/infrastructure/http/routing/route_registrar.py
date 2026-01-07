"""Route registration utilities."""

from fastapi import FastAPI
from .module_scanner import ModuleScanner, ServiceScanner
from .route_handlers import create_module_handler, create_service_handler


class RouteRegistrar:
    """Handles registration of routes to FastAPI app."""
    
    def __init__(self, app: FastAPI):
        """Initialize registrar with FastAPI app."""
        self.app = app
    
    def register_module_routes(self, package_name: str = "ncm.api.modules") -> int:
        """
        Register all module routes with @ncm_api decorator.
        
        Args:
            package_name: Package to scan for modules
            
        Returns:
            Number of registered routes
        """
        scanner = ModuleScanner(package_name)
        modules = scanner.scan_modules()
        
        registered_count = 0
        
        for module_path, func_name, func, route_info in modules:
            # Create FastAPI route handler
            handler = create_module_handler(func)
            
            # Generate tag from module path (e.g., "search.search" -> "Search")
            tag = module_path.split('.')[0].replace('_', ' ').title()
            
            # Generate unique name for the route
            route_name = f"{module_path.replace('.', '_')}_{func_name}"
            
            # Register route for each HTTP method
            for method in route_info['methods']:
                self.app.add_api_route(
                    path=route_info['path'],
                    endpoint=handler,
                    methods=[method.upper()],
                    name=f"{route_name}_{method.lower()}",
                    tags=[tag]
                )
            
            registered_count += 1
            methods_str = ", ".join(route_info['methods'])
            print(f"✓ Registered Module: [{methods_str}] {route_info['path']} -> {module_path}.{func_name}")
        
        if registered_count > 0:
            print(f"🚀 Successfully registered {registered_count} module endpoints\n")
        
        return registered_count
    
    def register_service_routes(self, package_name: str = "ncm.api.ncm") -> int:
        """
        Register all ncm routes with @ncm_service decorator.
        
        Args:
            package_name: Package to scan for services
            
        Returns:
            Number of registered routes
        """
        scanner = ServiceScanner(package_name)
        services = scanner.scan_services()
        
        registered_count = 0
        
        # Track service instances for cleanup on shutdown
        if not hasattr(self.app.state, "service_instances"):
            self.app.state.service_instances = []
        seen_instances = set()

        for modname, class_name, method_name, method, route_info in services:
            # Create FastAPI route handler for ncm method
            handler = create_service_handler(method)
            
            # Track bound instance if available
            inst = getattr(method, "__self__", None)
            if inst is not None and hasattr(inst, "cleanup"):
                if id(inst) not in seen_instances:
                    self.app.state.service_instances.append(inst)
                    seen_instances.add(id(inst))
            
            # Register route for each HTTP method
            for http_method in route_info['methods']:
                self.app.add_api_route(
                    path=route_info['path'],
                    endpoint=handler,
                    methods=[http_method.upper()],
                    name=f"controller_{modname}_{method_name}_{http_method.lower()}",
                    tags=[f"Controller - {class_name}"]
                )
            
            registered_count += 1
            methods_str = ", ".join(route_info['methods'])
            print(f"✓ Registered Controller: [{methods_str}] {route_info['path']} -> {class_name}.{method_name}")
        
        if registered_count > 0:
            print(f"🎯 Successfully registered {registered_count} ncm controllers\n")
        
        return registered_count
    
    def register_system_routes(self):
        """Register basic system routes (health check, root)."""
        
        @self.app.get("/health", tags=["System"])
        async def health_check():
            """Health check endpoint."""
            return {"status": "ok", "message": "NCM API Server is running"}
        
        @self.app.get("/", tags=["System"])
        async def root():
            """Root endpoint with basic information."""
            return {
                "name": "NCM Python API Server",
                "version": "0.1.0",
                "description": "网易云音乐 Python API 服务器",
                "docs": "/docs",
                "health": "/health"
            }


def auto_register_all_routes(app: FastAPI) -> dict:
    """
    Automatically register all routes (modules, services, system).
    
    Args:
        app: FastAPI application instance
        
    Returns:
        Dictionary with registration statistics
    """
    registrar = RouteRegistrar(app)
    
    # Register system routes first
    registrar.register_system_routes()
    
    # Register module routes
    module_count = registrar.register_module_routes()
    
    # Register ncm routes
    service_count = registrar.register_service_routes()
    
    total_count = module_count + service_count
    print(f"🎉 Total registered endpoints: {total_count}")
    
    return {
        "modules": module_count,
        "services": service_count,
        "total": total_count
    }
