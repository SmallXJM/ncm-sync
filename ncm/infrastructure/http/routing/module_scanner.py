"""Module and ncm scanning utilities."""

import importlib
import inspect
import pkgutil
from typing import List, Tuple, Any, Callable
from ncm.core.logging import get_logger

logger = get_logger(__name__)

class ModuleScanner:
    """Scanner for NCM API modules with @ncm_api decorator."""
    
    def __init__(self, package_name: str):
        """Initialize scanner with package name."""
        self.package_name = package_name
    
    def scan_modules(self) -> List[Tuple[str, str, Callable, dict]]:
        """
        Scan package for modules with @ncm_api decorated functions.
        
        Returns:
            List of tuples: (module_path, function_name, function, route_info)
        """
        results = []
        
        try:
            # Import the package
            package = importlib.import_module(self.package_name)
            
            # Recursively scan all modules and sub-packages
            self._scan_package_recursive(package, self.package_name, results)
                    
        except Exception as e:
            logger.error(f"✗ Failed to scan package {self.package_name}: {e}")
        
        return results
    
    def _scan_package_recursive(self, package, package_path: str, results: List[Tuple[str, str, Callable, dict]]):
        """
        Recursively scan a package and its sub-packages for @ncm_api decorated functions.
        
        Args:
            package: The imported package object
            package_path: Full dotted path to the package (e.g., "ncm.modules.search")
            results: List to append results to
        """
        try:
            # Scan all modules and sub-packages in the current package
            for importer, modname, ispkg in pkgutil.iter_modules(package.__path__):
                full_module_path = f"{package_path}.{modname}"
                
                if ispkg:
                    # It's a sub-package, scan it recursively
                    try:
                        sub_package = importlib.import_module(full_module_path)
                        self._scan_package_recursive(sub_package, full_module_path, results)
                    except Exception as e:
                        logger.error(f"✗ Failed to load sub-package {full_module_path}: {e}")
                else:
                    # It's a module, scan for decorated functions
                    try:
                        module = importlib.import_module(full_module_path)
                        
                        # Scan all functions in the module
                        for func_name, func in inspect.getmembers(module, inspect.isfunction):
                            if hasattr(func, '_ncm_route'):
                                route_info = func._ncm_route
                                # Use relative module path for better organization
                                relative_path = full_module_path.replace(f"{self.package_name}.", "")
                                results.append((relative_path, func_name, func, route_info))
                                
                    except Exception as e:
                        logger.error(f"✗ Failed to load module {full_module_path}: {e}")
                        
        except Exception as e:
            logger.error(f"✗ Failed to scan package {package_path}: {e}")


class ServiceScanner:
    """Scanner for NCM ncm classes with @ncm_service decorated methods."""
    
    def __init__(self, package_name: str):
        """Initialize scanner with package name."""
        self.package_name = package_name
    
    def scan_services(self) -> List[Tuple[str, str, str, Callable, dict]]:
        """
        Scan package for ncm classes with @ncm_service decorated methods.
        
        Returns:
            List of tuples: (module_name, class_name, method_name, method, route_info)
        """
        results = []
        
        try:
            # Import the package
            package = importlib.import_module(self.package_name)
            
            # Recursively scan all modules and sub-packages
            self._scan_service_package_recursive(package, self.package_name, results)
                    
        except Exception as e:
            # print(f"✗ Failed to scan services package {self.package_name}: {e}")
            logger.exception(f"✗ Failed to scan services package {self.package_name}: {e}")
        
        return results
    
    def _scan_service_package_recursive(self, package, package_path: str, results: List[Tuple[str, str, str, Callable, dict]]):
        """
        Recursively scan a package and its sub-packages for ncm classes with @ncm_service decorated methods.
        
        Args:
            package: The imported package object
            package_path: Full dotted path to the package (e.g., "ncm.ncm.auth")
            results: List to append results to
        """
        try:
            # Scan all modules and sub-packages in the current package
            for importer, modname, ispkg in pkgutil.iter_modules(package.__path__):
                full_module_path = f"{package_path}.{modname}"
                
                if ispkg:
                    # It's a sub-package, scan it recursively
                    try:
                        sub_package = importlib.import_module(full_module_path)
                        self._scan_service_package_recursive(sub_package, full_module_path, results)
                    except Exception as e:
                        logger.error(f"✗ Failed to load ncm sub-package {full_module_path}: {e}")
                else:
                    # It's a module, scan for ncm classes
                    try:
                        module = importlib.import_module(full_module_path)
                        
                        # Scan all classes in the module
                        for class_name, cls in inspect.getmembers(module, inspect.isclass):
                            if class_name.endswith('Controller'):
                                # Create ncm instance
                                try:
                                    service_instance = cls()
                                    
                                    # Scan all methods in the ncm class
                                    for method_name, method in inspect.getmembers(service_instance, inspect.ismethod):
                                        if hasattr(method, '_ncm_service_route'):
                                            route_info = method._ncm_service_route
                                            # Use relative module path for better organization
                                            relative_path = full_module_path.replace(f"{self.package_name}.", "")
                                            results.append((relative_path, class_name, method_name, method, route_info))
                                            
                                except Exception as e:
                                    logger.error(f"✗ Failed to instantiate ncm {class_name}: {e}")
                                
                    except Exception as e:
                        logger.error(f"✗ Failed to load ncm module {full_module_path}: {e}")
                        
        except Exception as e:
            logger.exception(f"✗ Failed to scan ncm package {package_path}: {e}")
