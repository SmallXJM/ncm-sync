from __future__ import annotations

from typing import Optional

from ncm.service.download.service.async_task_service import AsyncTaskService
from .base import BaseMusicService
from .detail import DetailService
from .cover import CoverService
from .stream import StreamService



class LocalMusicService(DetailService, CoverService, StreamService):
    """
    Unified service for local music operations.
    Combines functionality from DetailService, CoverService, and StreamService.
    """

    def __init__(self, task_service: Optional[AsyncTaskService] = None):
        super().__init__(task_service)
