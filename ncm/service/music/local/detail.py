from pathlib import Path
from typing import Optional, Union

from ncm.core.logging import get_logger
from .base import BaseMusicService
from ncm.service.music.utils import is_within, extract_lyrics

logger = get_logger(__name__)


class DetailService(BaseMusicService):
    """Service for handling music details and management."""

    async def get_detail(self, task_id: int) -> dict:
        """Get music task details including lyrics."""
        task = await self._task_service.get_task(int(task_id))
        if not task:
            return {
                "status": 404,
                "body": {
                    "code": 404,
                    "message": "Task not found",
                },
            }

        file_path = Path(task.file_path) if task.file_path else None
        file_exists = bool(file_path and file_path.exists())

        lyrics = None
        if file_exists and file_path:
            lyrics = extract_lyrics(file_path)

        return {
            "status": 200,
            "body": {
                "code": 200,
                "message": "OK",
                "data": {
                    "id": task.id,
                    "music_id": task.music_id,
                    "music_title": task.music_title,
                    "music_artist": task.music_artist,
                    "music_album": task.music_album,
                    "quality": task.quality,
                    "file_path": task.file_path,
                    "file_name": task.file_name,
                    "file_format": task.file_format,
                    "file_size": task.file_size,
                    "status": task.status,
                    "error_message": task.error_message,
                    "lyrics": lyrics,
                    "file_exists": file_exists,
                },
            },
        }

    async def delete(self, task_id: Optional[Union[int, str]]) -> dict:
        """Delete local music file."""
        if not task_id:
            return {
                "status": 400,
                "body": {"code": 400, "message": "task_id required"},
            }

        task = await self._task_service.get_task(int(task_id))
        if not task or not task.file_path:
            return {
                "status": 404,
                "body": {"code": 404, "message": "Task/file not found"},
            }

        job = await self._task_service.get_job_for_task(int(task_id))
        if not job:
            return {
                "status": 404,
                "body": {"code": 404, "message": "Job not found"},
            }

        file_path = Path(task.file_path)
        base = Path(job.storage_path)
        if not is_within(file_path, base):
            return {
                "status": 403,
                "body": {"code": 403, "message": "Forbidden"},
            }

        try:
            if file_path.exists():
                file_path.unlink()
            await self._task_service.update_fields(int(task_id), file_path=None, file_name=None, file_size=None)
            return {
                "status": 200,
                "body": {"code": 200, "message": "OK"},
            }
        except Exception as e:
            logger.exception("Failed to delete local music file")
            return {
                "status": 500,
                "body": {"code": 500, "message": str(e)},
            }

    async def rename(self, task_id: Optional[Union[int, str]], new_name: Optional[str]) -> dict:
        """Rename local music file."""
        if not task_id or not new_name:
            return {
                "status": 400,
                "body": {"code": 400, "message": "task_id and new_name required"},
            }

        task = await self._task_service.get_task(int(task_id))
        if not task or not task.file_path:
            return {
                "status": 404,
                "body": {"code": 404, "message": "Task/file not found"},
            }

        job = await self._task_service.get_job_for_task(int(task_id))
        if not job:
            return {
                "status": 404,
                "body": {"code": 404, "message": "Job not found"},
            }

        file_path = Path(task.file_path)
        base = Path(job.storage_path)
        if not is_within(file_path, base):
            return {
                "status": 403,
                "body": {"code": 403, "message": "Forbidden"},
            }

        if not file_path.exists():
            return {
                "status": 404,
                "body": {"code": 404, "message": "File not found"},
            }

        target_path = file_path.with_name(str(new_name))
        if not is_within(target_path, base):
            return {
                "status": 403,
                "body": {"code": 403, "message": "Forbidden"},
            }

        try:
            file_path.rename(target_path)
            await self._task_service.update_fields(
                int(task_id),
                file_path=str(target_path),
                file_name=target_path.name,
            )
            updated = await self._task_service.get_task(int(task_id))
            return {
                "status": 200,
                "body": {
                    "code": 200,
                    "message": "OK",
                    "data": updated.to_dict() if updated else None,
                },
            }
        except Exception as e:
            logger.exception("Failed to rename local music file")
            return {
                "status": 500,
                "body": {"code": 500, "message": str(e)},
            }
