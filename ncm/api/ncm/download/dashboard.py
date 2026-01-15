"""Music download controller with new task-driven architecture."""

from ncm.api.ncm.download import DownloadContext
from ncm.core.options import APIResponse
from ncm.core.logging import get_logger
from ncm.infrastructure.http import ncm_service

logger = get_logger(__name__)


class DownloadControllerDashboard:
    def __init__(self, context: DownloadContext):
        # self.ctx = context
        self.orchestrator = context.orchestrator
        self._scheduler = context.scheduler
        self.process = context.process

    