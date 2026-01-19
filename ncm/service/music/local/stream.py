from pathlib import Path

from .base import BaseMusicService
from ncm.service.music.utils import guess_audio_mime
from ncm.service.music.exceptions import LocalMusicNotFoundError


class StreamService(BaseMusicService):
    """Service for handling music streaming."""

    async def get_stream(self, task_id: int) -> dict:
        """Get stream information for music task."""
        task = await self._task_service.get_task(int(task_id))
        if not task or not task.file_path:
            raise LocalMusicNotFoundError("not found")

        file_path = Path(task.file_path)
        if not file_path.exists():
            raise LocalMusicNotFoundError("not found")

        media_type = guess_audio_mime(file_path)
        return {
            "file_path": file_path,
            "media_type": media_type,
        }
