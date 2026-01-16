from __future__ import annotations

from typing import Any, Dict, Optional, Callable, Awaitable

import asyncio

from ncm.core.logging import get_logger
from .base import DownloadWsContext, WsModule, WsModuleRegistry, SnapshotDiffer, SnapshotDiffConfig

logger = get_logger(__name__)


class SchedulerWsModule:
    name = "scheduler"

    def __init__(self, context: DownloadWsContext) -> None:
        self._context = context
        self._differ = SnapshotDiffer(
            name=self.name,
            config=SnapshotDiffConfig(
                max_depth=None,
                ignore_fields=None,
                debug=False,
                custom_equal=None,
            ),
        )
        self._subscribed = False
        self._event = asyncio.Event()
        self._interval = 0.5

    async def get_payload(self) -> Optional[Dict[str, Any]]:
        process_status = self._context.process.get_status()
        scheduler_stats = self._context.scheduler.get_stats()
        current_speed = self._context.orchestrator.get_current_speed()
        snapshot = {
            "is_running": process_status["running"],
            "started_at" : process_status["started_at"],
            "finished_at" : process_status["finished_at"],
            "next_run_at" : scheduler_stats["next_run_time"],
            "current_speed": current_speed,
        }
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

            snapshot = await self.get_payload()

            if not self._differ.has_changed(snapshot):
                continue

            await send({self.name: snapshot})


def register_ws_modules(registry: WsModuleRegistry) -> None:
    module: WsModule = SchedulerWsModule(registry.context)
    registry.register(module)
