from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol, Iterable, Callable, Set, Tuple, Awaitable

import hashlib
import json
import time

from ncm.core.logging import get_logger

logger = get_logger(__name__)

from ncm.service.download.orchestrator import DownloadOrchestrator, DownloadProcess
from ncm.service.download.orchestrator.scheduler import ProcessScheduler

@dataclass
class DownloadWsContext:
    orchestrator: DownloadOrchestrator
    process: DownloadProcess
    scheduler: ProcessScheduler


class WsModule(Protocol):
    name: str

    async def run(self, send: Callable[[Dict[str, Any]], Awaitable[None]]) -> None:
        ...

    def on_subscribe(self) -> None:
        ...

    def on_unsubscribe(self) -> None:
        ...

    async def get_payload(self) -> Optional[Dict[str, Any]]:
        ...

    async def handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        ...


class WsModuleRegistry:
    def __init__(self, context: DownloadWsContext) -> None:
        self._context = context
        self._modules: Dict[str, WsModule] = {}

    @property
    def context(self) -> DownloadWsContext:
        return self._context

    def register(self, module: WsModule) -> None:
        self._modules[module.name] = module

    def get(self, name: str) -> Optional[WsModule]:
        return self._modules.get(name)

    def clear(self) -> None:
        self._modules.clear()

    def names(self) -> Iterable[str]:
        return list(self._modules.keys())


@dataclass
class SnapshotDiffConfig:
    max_depth: Optional[int] = None
    ignore_fields: Optional[Set[str]] = None
    debug: bool = False
    custom_equal: Optional[Callable[[Any, Any, str], Optional[bool]]] = None


@dataclass
class SnapshotDiffStats:
    checks: int = 0
    changes: int = 0
    first_check_ts: float = 0.0


class SnapshotDiffer:
    def __init__(self, name: str, config: Optional[SnapshotDiffConfig] = None) -> None:
        self._name = name
        self._config = config or SnapshotDiffConfig()
        self._last_snapshot: Any = None
        self._last_hash: Optional[str] = None
        self._stats = SnapshotDiffStats()

    @property
    def stats(self) -> SnapshotDiffStats:
        return self._stats

    def _compute_hash(self, snapshot: Any) -> str:
        try:
            payload = json.dumps(snapshot, sort_keys=True, ensure_ascii=False, default=str)
        except Exception:
            payload = repr(snapshot)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _is_ignored(self, path: str) -> bool:
        ignore = self._config.ignore_fields
        if not ignore:
            return False
        if path in ignore:
            return True
        if "." in path and path.split(".")[-1] in ignore:
            return True
        return False

    def _deep_diff(self, old: Any, new: Any, path: str = "", depth: int = 0) -> Tuple[bool, Optional[str]]:
        if self._config.max_depth is not None and depth > self._config.max_depth:
            return (old != new, path)

        if self._config.custom_equal is not None:
            try:
                result = self._config.custom_equal(old, new, path)
                if isinstance(result, bool):
                    return (not result, path if not result else None)
            except Exception as exc:
                logger.error(f"SnapshotDiffer custom_equal error at {path}: {exc}")

        if self._is_ignored(path):
            return (False, None)

        if type(old) is not type(new):
            return (True, path)

        if isinstance(old, dict):
            old_keys = set(old.keys())
            new_keys = set(new.keys())
            if old_keys != new_keys:
                return (True, path)
            for key in old_keys:
                child_path = f"{path}.{key}" if path else str(key)
                changed, changed_path = self._deep_diff(old[key], new[key], child_path, depth + 1)
                if changed:
                    return (True, changed_path)
            return (False, None)

        if isinstance(old, (list, tuple)):
            if len(old) != len(new):
                return (True, path)
            for index, (ov, nv) in enumerate(zip(old, new)):
                child_path = f"{path}[{index}]" if path else f"[{index}]"
                changed, changed_path = self._deep_diff(ov, nv, child_path, depth + 1)
                if changed:
                    return (True, changed_path)
            return (False, None)

        if old != new:
            return (True, path)

        return (False, None)

    def reset(self) -> None:
        self._last_snapshot = None
        self._last_hash = None
        self._stats = SnapshotDiffStats()

    def has_changed(self, snapshot: Any) -> bool:
        now = time.time()
        if self._stats.first_check_ts == 0.0:
            self._stats.first_check_ts = now
        self._stats.checks += 1

        if self._last_snapshot is None:
            self._last_snapshot = snapshot
            self._last_hash = self._compute_hash(snapshot)
            self._stats.changes += 1
            if self._config.debug:
                logger.info(f"SnapshotDiffer[{self._name}] initial snapshot recorded")
            return True

        new_hash = self._compute_hash(snapshot)
        if self._last_hash == new_hash:
            if self._config.debug:
                logger.debug(f"SnapshotDiffer[{self._name}] hash unchanged")
            return False

        changed, changed_path = self._deep_diff(self._last_snapshot, snapshot)
        if not changed:
            self._last_hash = new_hash
            if self._config.debug:
                logger.debug(f"SnapshotDiffer[{self._name}] deep diff no changes")
            return False

        self._last_snapshot = snapshot
        self._last_hash = new_hash
        self._stats.changes += 1

        if self._config.debug:
            elapsed = now - self._stats.first_check_ts if self._stats.first_check_ts > 0 else 0.0
            frequency = float(self._stats.changes) / elapsed if elapsed > 0 else 0.0
            logger.info(
                f"SnapshotDiffer[{self._name}] change detected at {changed_path}, "
                f"checks={self._stats.checks}, changes={self._stats.changes}, "
                f"freq={frequency:.2f}/s"
            )

        return True
