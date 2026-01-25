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

from ncm.core.path import get_cache_path, prepare_path, sanitize_filename
from ncm.core.constants import COVER_CACHE_DIR_NAME

logger = get_logger(__name__)

CACHE_DIR = get_cache_path(COVER_CACHE_DIR_NAME)
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

    def _get_cache_key(self, artist: str, album: str) -> str:
        """Generate cache key from artist and album."""
        safe_artist = sanitize_filename(artist) or "Unknown Artist"
        safe_album = sanitize_filename(album) or "Unknown Album"
        return f"{safe_artist}/{safe_album}"

    async def _get_lock(self, key: str) -> asyncio.Lock:
        """Get or create a lock for a specific cache key."""
        async with self._locks_lock:
            if key not in self._locks:
                self._locks[key] = asyncio.Lock()
            return self._locks[key]

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
            # Recursively walk through cache directory
            for root, dirs, files in os.walk(self._cache_dir):
                for file in files:
                    file_path = Path(root) / file
                    try:
                        if now - file_path.stat().st_mtime > CACHE_EXPIRY_SECONDS:
                            file_path.unlink()
                            logger.debug(f"Deleted expired cache: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete expired cache {file_path}: {e}")
                
                # Try to remove empty directories (bottom-up is not guaranteed by os.walk unless topdown=False)
                # But here we just try to clean up what we can.
                
            # Second pass to remove empty directories
            for root, dirs, files in os.walk(self._cache_dir, topdown=False):
                 for dir_name in dirs:
                    dir_path = Path(root) / dir_name
                    try:
                        if not any(dir_path.iterdir()):
                             dir_path.rmdir()
                    except Exception:
                        pass
                        
        except Exception as e:
             logger.error(f"Error scanning cache dir: {e}")

    def _get_cache_path(self, artist: str, album: str) -> Path:
        """Get base path for cache file (without extension)."""
        safe_artist = sanitize_filename(artist) or "Unknown Artist"
        safe_album = sanitize_filename(album) or "Unknown Album"
        return self._cache_dir / safe_artist / safe_album

    def _find_cached_file(self, artist: str, album: str) -> Optional[Path]:
        """Find cached file for artist/album (checking supported extensions)."""
        base_path = self._get_cache_path(artist, album)
        for ext in [".jpg", ".png", ".jpeg"]:
            p = base_path.with_suffix(ext)
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

    async def _save_to_cache(self, artist: str, album: str, data: bytes, media_type: str):
        """Save cover to cache asynchronously."""
        ext = ".jpg"
        if media_type == "image/png":
            ext = ".png"
        elif media_type == "image/jpeg":
            ext = ".jpg"

        base_path = self._get_cache_path(artist, album)
        path = base_path.with_suffix(ext)
        
        # Ensure parent directory exists
        prepare_path(path)

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

        # Use music_album and music_artist if available, otherwise fallback to music_id/task_id
        artist = task.music_artist or "Unknown Artist"
        album = task.music_album or task.music_id or f"task_{task_id}"
        
        # 1. Check cache
        cached_file = self._find_cached_file(artist, album)
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
        lock_key = self._get_cache_key(artist, album)
        lock = await self._get_lock(lock_key)
        async with lock:
            # Double check cache
            cached_file = self._find_cached_file(artist, album)
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
            await self._save_to_cache(artist, album, cover, media_type)

            return {
                "content": cover,
                "media_type": media_type,
            }
