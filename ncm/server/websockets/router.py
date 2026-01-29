from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from fastapi import WebSocket, WebSocketDisconnect

from ncm.core.logging import get_logger
from .base import DownloadWsContext, WsModuleRegistry
from .loader import load_ws_modules

logger = get_logger(__name__)


class WsRouter:
    def __init__(self, context: DownloadWsContext) -> None:
        self._context = context
        self._registry = WsModuleRegistry(context)
        load_ws_modules(self._registry, reload=False)

    async def handle(self, websocket: WebSocket) -> None:
        await websocket.accept()
        send_lock = asyncio.Lock()

        async def safe_send(payload: Dict[str, Any]) -> None:
            try:
                async with send_lock:
                    await websocket.send_json(payload)
            except Exception as exc:
                logger.error(f"WS send error: {exc}")


        runners: List[asyncio.Task[Any]] = []

        def restart_runners() -> None:
            nonlocal runners
            for task in runners:
                task.cancel()
            runners = []
            for name in self._registry.names():
                module = self._registry.get(name)
                if module is None:
                    continue
                runners.append(asyncio.create_task(module.run(safe_send)))

        restart_runners()

        try:
            while True:
                try:
                    message = await websocket.receive_json()
                except WebSocketDisconnect:
                    break
                except Exception as exc:
                    logger.error(f"WebSocket receive error: {exc}")
                    break

                if not isinstance(message, dict):
                    continue

                subscribe_target = message.get("subscribe")
                if subscribe_target == "all":
                    for name in self._registry.names():
                        module = self._registry.get(name)
                        if module is not None:
                            module.on_subscribe()
                    logger.debug("WS subscribe all modules")
                elif subscribe_target == "none":
                    for name in self._registry.names():
                        module = self._registry.get(name)
                        if module is not None:
                            module.on_unsubscribe()
                    logger.debug("WS clear all subscriptions")
                elif isinstance(subscribe_target, str):
                    module = self._registry.get(subscribe_target)
                    if module is not None:
                        module.on_subscribe()
                        logger.debug(f"WS subscribe module: {subscribe_target}")

                unsubscribe_target = message.get("unsubscribe")
                if unsubscribe_target == "all":
                    for name in self._registry.names():
                        module = self._registry.get(name)
                        if module is not None:
                            module.on_unsubscribe()
                    logger.debug("WS unsubscribe all modules")
                elif isinstance(unsubscribe_target, str):
                    module = self._registry.get(unsubscribe_target)
                    if module is not None:
                        module.on_unsubscribe()
                        logger.debug(f"WS unsubscribe module: {unsubscribe_target}")

                if message.get("reload") is True:
                    load_ws_modules(self._registry, reload=True)
                    restart_runners()

                module_name = message.get("module")
                if isinstance(module_name, str):
                    module = self._registry.get(module_name)
                    if module is not None:
                        try:
                            response = await module.handle_message(message)
                        except Exception as exc:
                            logger.error(f"WS module {module_name} handle_message error: {exc}")
                            response = None
                        if response is not None:
                            await safe_send(response)
        finally:
            for task in runners:
                task.cancel()
            try:
                await websocket.close()
            except Exception:
                pass
