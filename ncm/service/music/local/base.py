from pathlib import Path
from typing import Optional

from ncm.service.download.service.async_task_service import AsyncTaskService


class BaseMusicService:
    """Base service for local music operations."""

    def __init__(self, task_service: Optional[AsyncTaskService] = None):
        self._task_service = task_service or AsyncTaskService()
