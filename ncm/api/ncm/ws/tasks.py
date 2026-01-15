from __future__ import annotations

from typing import Any, Dict, Optional, Callable, Awaitable

import asyncio

from ncm.core.logging import get_logger
from .base import DownloadWsContext, WsModule, WsModuleRegistry, SnapshotDiffer, SnapshotDiffConfig

logger = get_logger(__name__)


class TasksWsModule:
    name = "tasks"

    def __init__(self, context: DownloadWsContext) -> None:
        self._context = context
        self._differ = SnapshotDiffer(
            name="tasks",
            config=SnapshotDiffConfig(
                max_depth=None,
                ignore_fields=None,
                debug=False,
                custom_equal=None,
            ),
        )
        self._subscribed = False
        self._event = asyncio.Event()
        self._interval = 1.0

    async def get_payload(self) -> Optional[Dict[str, Any]]:
        active_tasks = await self._context.orchestrator.list_active_tasks_dict()
        snapshot = {
            "items": list(active_tasks.values()),
            "count": len(active_tasks),
        }
        if not self._differ.has_changed(snapshot):
            return None
        return snapshot

    async def handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return None

    def on_subscribe(self) -> None:
        self._subscribed = True
        self._event.set()

    def on_unsubscribe(self) -> None:
        self._subscribed = False
        self._differ.reset()

    async def run(self, send: Callable[[Dict[str, Any]], Awaitable[None]]) -> None:
        while True:
            await asyncio.sleep(self._interval)

            if not self._subscribed:
                self._event.clear()
                await self._event.wait()


            if not self._subscribed:
                continue

            active_tasks = await self._context.orchestrator.list_active_tasks_dict()
            snapshot = {
                "items": list(active_tasks.values()),
                "count": len(active_tasks),
            }
            if not self._differ.has_changed(snapshot):
                continue

            await send({"tasks": snapshot})


def register_ws_modules(registry: WsModuleRegistry) -> None:
    module: WsModule = TasksWsModule(registry.context)
    registry.register(module)
