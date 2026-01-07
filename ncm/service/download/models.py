"""Unified data models for download service."""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import asyncio
from ncm.core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class DownloadTask:
    """统一的下载任务模型 - 消除数据冗余"""

    # 基本信息
    id: int = 0
    music_id: str = ""
    storage_location_id: int = 0
    quality: str = 'lossless'
    custom_filename: Optional[str] = None

    # 下载信息
    url: str = ""
    file_path: Optional[Path] = None
    file_size: int = 0
    md5_hash: str = ""

    # 状态和进度
    status: str = "pending"  # pending, downloading, metadata, storing, completed, failed, cancelled
    progress: float = 0.0
    downloaded_bytes: int = 0

    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 下载分段信息 (内部使用)
    segments: List[Dict] = field(default_factory=list)
    temp_dir: Optional[Path] = None

    # 结果信息
    success: bool = False
    error_message: Optional[str] = None

    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    def update_progress(self):
        """更新总体进度"""
        if self.file_size > 0:
            self.progress = self.downloaded_bytes / self.file_size
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "task_id": self.id,
            "music_id": self.music_id,
            "storage_location_id": self.storage_location_id,
            "quality": self.quality,
            "status": self.status,
            "progress": self.progress,
            "success": self.success,
            "file_path": str(self.file_path) if self.file_path else None,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            # 元数据字段 (向后兼容)
            "title": self.metadata.get("title"),
            "artist": self.metadata.get("artist"),
            "filename": self.custom_filename,
            "file_format": self.metadata.get("file_format"),
            "file_size": self.file_size,
            "bitrate": self.metadata.get("bitrate"),
            "download_url": self.url,
        }


class DownloadDataCache:
    def __init__(self, task_id: int, music_id: str):
        self.task_id = task_id
        self.music_id = music_id
        self.song_detail: Optional[Dict[str, Any]] = None
        self.play_url: Optional[Dict[str, Any]] = None
        self._detail_ts: Optional[datetime] = None
        self._url_ts: Optional[datetime] = None
        self._lock = asyncio.Lock()

    async def ensure_song_detail(self, loader, force: bool = False) -> Dict[str, Any]:
        async with self._lock:
            if self.song_detail is None or force:
                resp = await loader(ids=self.music_id)
                if not getattr(resp, "success", False):
                    raise RuntimeError("song_detail request failed")
                body = getattr(resp, "body", {})
                songs = body.get("songs") or []
                if not songs:
                    raise RuntimeError("song_detail invalid")
                self.song_detail = songs[0]
                self._detail_ts = datetime.utcnow()
            return self.song_detail

    async def ensure_play_url(self, loader, level: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
        async with self._lock:
            if self.play_url is None or force:
                if level is not None:
                    resp = await loader(id=self.music_id, level=level)
                else:
                    resp = await loader(id=self.music_id)
                if not getattr(resp, "success", False):
                    raise RuntimeError("play_url request failed")
                body = getattr(resp, "body", {})
                data = body.get("data") or []
                if not data:
                    raise RuntimeError("play_url invalid")
                item = data[0]
                if not item.get("url") or item.get("code") != 200:
                    raise RuntimeError("play_url invalid")
                self.play_url = item
                self._url_ts = datetime.utcnow()
            return self.play_url

    def clear(self):
        self.song_detail = None
        self.play_url = None
        self._detail_ts = None
        self._url_ts = None


class TaskCacheRegistry:
    def __init__(self):
        self._caches: Dict[int, DownloadDataCache] = {}
        self._lock = asyncio.Lock()

    async def get_or_create(self, task_id: int, music_id: str) -> DownloadDataCache:
        async with self._lock:
            cache = self._caches.get(task_id)
            if cache is None:
                cache = DownloadDataCache(task_id, music_id)
                self._caches[task_id] = cache
            return cache

    def get(self, task_id: int) -> Optional[DownloadDataCache]:
        return self._caches.get(task_id)

    async def prefetch(self, task_id: int, music_id: str) -> DownloadDataCache:
        """提前准备数据，用于刚启动时"""
        cache = await self.get_or_create(task_id, music_id)
        return cache

    def clear(self, task_id: int) -> None:
        cache = self._caches.pop(task_id, None)
        if cache:
            cache.clear()
        logger.debug(f"clear cache registry task {task_id}")


_registry: Optional[TaskCacheRegistry] = None


def get_task_cache_registry() -> TaskCacheRegistry:
    global _registry
    if _registry is None:
        _registry = TaskCacheRegistry()
    return _registry
