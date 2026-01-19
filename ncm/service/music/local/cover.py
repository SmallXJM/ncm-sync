import asyncio
import os
import time
from pathlib import Path
from typing import Optional

from ncm.core.logging import get_logger
from ncm.service.download.service.async_task_service import AsyncTaskService
from .base import BaseMusicService
from ncm.service.music.utils import extract_cover_bytes, guess_image_mime
from ncm.service.music.exceptions import LocalMusicNotFoundError, LocalMusicNoCoverError

from ncm.core.path import get_data_path, prepare_path

logger = get_logger(__name__)

CACHE_DIR = get_data_path("cache/cover")
CACHE_EXPIRY_SECONDS = 7 * 24 * 3600  # 7 days


class CoverService(BaseMusicService):
    """Service for handling music cover art with caching."""

    def __init__(self, task_service: Optional[AsyncTaskService] = None):
        super().__init__(task_service)
        self._cache_dir = CACHE_DIR
        prepare_path(self._cache_dir)
        self._locks = {}  # music_id -> Lock
        self._locks_lock = asyncio.Lock()

    def _ensure_cache_dir(self):
        """Ensure cache directory exists."""
        # Deprecated: Handled by prepare_path in init
        pass

    async def _get_lock(self, music_id: str) -> asyncio.Lock:
        """Get or create a lock for a specific music ID."""
        async with self._locks_lock:
            if music_id not in self._locks:
                self._locks[music_id] = asyncio.Lock()
            return self._locks[music_id]

    async def _cleanup_cache(self):
        """Cleanup expired cache files."""
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._cleanup_cache_sync)
        except Exception as e:
            logger.error(f"Failed to cleanup cache: {e}")

    def _cleanup_cache_sync(self):
        if not self._cache_dir.exists():
            return

        now = time.time()
        try:
            for entry in os.scandir(self._cache_dir):
                if not entry.is_file():
                    continue
                try:
                    if now - entry.stat().st_mtime > CACHE_EXPIRY_SECONDS:
                        os.unlink(entry.path)
                        logger.debug(f"Deleted expired cache: {entry.path}")
                except Exception as e:
                    logger.warning(f"Failed to delete expired cache {entry.path}: {e}")
        except Exception as e:
             logger.error(f"Error scanning cache dir: {e}")

    def _find_cached_file(self, music_id: str) -> Optional[Path]:
        """Find cached file for music_id (checking supported extensions)."""
        for ext in [".jpg", ".png", ".jpeg"]:
            p = self._cache_dir / f"{music_id}{ext}"
            if p.exists():
                return p
        return None

    async def _read_file(self, path: Path) -> bytes:
        """Read file asynchronously."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, path.read_bytes)

    async def _extract_cover_async(self, path: Path) -> Optional[bytes]:
        """Extract cover asynchronously."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, extract_cover_bytes, path)

    async def _save_to_cache(self, music_id: str, data: bytes, media_type: str):
        """Save cover to cache asynchronously."""
        ext = ".jpg"
        if media_type == "image/png":
            ext = ".png"
        elif media_type == "image/jpeg":
            ext = ".jpg"

        filename = f"{music_id}{ext}"
        path = self._cache_dir / filename

        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._write_file_sync, path, data)
        except Exception as e:
            logger.error(f"Failed to save cache {path}: {e}")

    def _write_file_sync(self, path: Path, data: bytes):
        """Write file atomically."""
        tmp_path = path.with_suffix(f".tmp.{time.time()}")
        try:
            tmp_path.write_bytes(data)
            tmp_path.replace(path)
        except Exception as e:
            if tmp_path.exists():
                tmp_path.unlink()
            raise e

    async def get_cover(self, task_id: int) -> dict:
        """Get cover art for music task, using cache if available."""
        # Probabilistic cleanup (1% chance)
        # if random.random() < 0.01:
        #     asyncio.create_task(self._cleanup_cache())

        task = await self._task_service.get_task(int(task_id))
        if not task or not task.file_path:
            raise LocalMusicNotFoundError("not found")

        # Use music_id if available, otherwise task_id
        music_id = str(task.music_id) if task.music_id else f"task_{task_id}"

        # 1. Check cache
        cached_file = self._find_cached_file(music_id)
        if cached_file:
            try:
                content = await self._read_file(cached_file)
                media_type = guess_image_mime(content)
                return {
                    "content": content,
                    "media_type": media_type,
                }
            except Exception as e:
                logger.warning(f"Failed to read cache {cached_file}: {e}")
                # Continue to extraction

        file_path = Path(task.file_path)
        if not file_path.exists():
            raise LocalMusicNotFoundError("not found")

        # 2. Extract with lock
        lock = await self._get_lock(music_id)
        async with lock:
            # Double check cache
            cached_file = self._find_cached_file(music_id)
            if cached_file:
                try:
                    content = await self._read_file(cached_file)
                    media_type = guess_image_mime(content)
                    return {
                        "content": content,
                        "media_type": media_type,
                    }
                except Exception:
                    pass

            # Extract
            cover = await self._extract_cover_async(file_path)
            if not cover:
                raise LocalMusicNoCoverError("no cover")

            media_type = guess_image_mime(cover)

            # Save to cache
            await self._save_to_cache(music_id, cover, media_type)

            return {
                "content": cover,
                "media_type": media_type,
            }
