from __future__ import annotations

import importlib
import pkgutil
from types import ModuleType
from typing import Dict

from ncm.core.logging import get_logger
from .base import WsModuleRegistry

logger = get_logger(__name__)

_LOADED_MODULES: Dict[str, ModuleType] = {}


def load_ws_modules(registry: WsModuleRegistry, reload: bool = False) -> None:
    package_name = "ncm.api.ncm.ws"
    try:
        package = importlib.import_module(package_name)
    except Exception as exc:
        logger.error(f"Failed to import ws package {package_name}: {exc}")
        return

    registry.clear()

    for _, modname, ispkg in pkgutil.iter_modules(package.__path__):
        if ispkg:
            continue
        if modname.startswith("_") or modname in {"base", "loader", "router"}:
            continue

        full_name = f"{package_name}.{modname}"

        try:
            module: ModuleType
            if reload and full_name in _LOADED_MODULES:
                module = importlib.reload(_LOADED_MODULES[full_name])
            else:
                module = importlib.import_module(full_name)
            _LOADED_MODULES[full_name] = module
        except Exception as exc:
            logger.error(f"Failed to import ws module {full_name}: {exc}")
            continue

        register_func = getattr(module, "register_ws_modules", None)
        if callable(register_func):
            try:
                register_func(registry)
            except Exception as exc:
                logger.error(f"Failed to register ws modules from {full_name}: {exc}")

