from __future__ import annotations

from typing import Any, Dict, Optional, Callable, Awaitable

import asyncio
import random
import time

try:
    import psutil
except ImportError:  # pragma: no cover - optional until dependencies are installed
    psutil = None

from ncm.core.logging import get_logger
from .base import DownloadWsContext, WsModule, WsModuleRegistry, SnapshotDiffer, SnapshotDiffConfig

logger = get_logger(__name__)


class SystemDownloadSpeedSampler:
    def __init__(self) -> None:
        self._last_bytes_recv: Optional[int] = None
        self._last_sample_time: Optional[float] = None
        self._missing_dependency_logged = False

    def get_current_speed(self) -> int:
        if psutil is None:
            if not self._missing_dependency_logged:
                logger.warning("psutil is not installed; system download speed will be reported as 0")
                self._missing_dependency_logged = True
            return 0

        try:
            counters = psutil.net_io_counters(pernic=False)
            now = time.monotonic()
            bytes_recv = int(max(0, counters.bytes_recv))

            if self._last_bytes_recv is None or self._last_sample_time is None:
                self._last_bytes_recv = bytes_recv
                self._last_sample_time = now
                return 0

            elapsed = now - self._last_sample_time
            delta = bytes_recv - self._last_bytes_recv
            self._last_bytes_recv = bytes_recv
            self._last_sample_time = now

            if elapsed <= 0 or delta <= 0:
                return 0

            return int(delta / elapsed)
        except Exception as e:
            logger.warning(f"Error getting system download speed: {e}")
            return 0


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
        self._system_speed_sampler = SystemDownloadSpeedSampler()
        # 临时演示数据：用平滑随机速度替代真实下载速度，便于观察仪表盘趋势图效果。
        self._mock_speed = 0
        self._mock_direction = 1

    async def get_payload(self) -> Optional[Dict[str, Any]]:
        process_status = self._context.process.get_status()
        scheduler_stats = self._context.scheduler.get_stats()
        # current_speed = self._get_mock_speed()
        current_speed = self._context.orchestrator.get_current_speed()
        system_download_speed = self._system_speed_sampler.get_current_speed()
        snapshot = {
            "is_running": process_status["running"],
            "started_at" : process_status["started_at"],
            "finished_at" : process_status["finished_at"],
            "next_run_at" : scheduler_stats["next_run_time"],
            "current_speed": current_speed,
            "system_download_speed": system_download_speed,
        }
        return snapshot

    def _get_mock_speed(self) -> int:
        """Generate a smooth mock download speed for dashboard preview."""
        if self._mock_speed <= 0:
            self._mock_speed = random.randint(2 * 1024 * 1024, 6 * 1024 * 1024)

        if random.random() < 0.18:
            self._mock_direction *= -1

        delta = random.randint(180 * 1024, 900 * 1024) * self._mock_direction
        next_speed = self._mock_speed + delta

        floor = 220 * 1024
        ceiling = 14 * 1024 * 1024
        if next_speed < floor or next_speed > ceiling:
            self._mock_direction *= -1
            next_speed = self._mock_speed + random.randint(120 * 1024, 640 * 1024) * self._mock_direction

        self._mock_speed = max(floor, min(ceiling, next_speed))
        return int(self._mock_speed)

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
