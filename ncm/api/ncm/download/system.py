"""Music download controller with new task-driven architecture."""

from ncm.api.ncm.download import DownloadContext
from ncm.core.options import APIResponse
from ncm.core.logging import get_logger
from ncm.infrastructure.http import ncm_service

logger = get_logger(__name__)


class DownloadControllerSystem:
    def __init__(self, context: DownloadContext):
        # self.ctx = context
        self.orchestrator = context.orchestrator
        self._scheduler = context.scheduler
        self.process = context.process

    async def get_stats(self, type: str, **kwargs) -> APIResponse:
        """
        Unified status query endpoint.

        Args:
            type: Status type ('system', 'process','scheduler','active_tasks')
        """
        try:
            if type == "system":
                data = {
                    "orchestrator": await self.orchestrator.get_stats(),
                    "process": self.process.get_status(),
                    "scheduler": self._scheduler.get_stats(),
                    "active_tasks": await self.orchestrator.list_active_tasks_dict()
                }
            elif type == "orchestrator":
                data = await self.orchestrator.get_stats()
            elif type == "process":
                data = self.process.get_status()
            elif type == "scheduler":
                data = self._scheduler.get_stats()
            elif type == "active_tasks":
                active_tasks_data = await self.orchestrator.list_active_tasks_dict()
                data = {
                    "tasks": list(active_tasks_data.values()),
                    "count": len(active_tasks_data)
                }
            else:
                return APIResponse(
                    status=400,
                    body={
                        "code": 400,
                        "message": f"Invalid stats type: {type}. Expected 'system', 'process', or 'active_tasks'."
                    }
                )

            return APIResponse(
                status=200,
                body={
                    "code": 200,
                    "message": "success",
                    "data": data
                }
            )

        except Exception as e:
            logger.exception(f"Failed to get stats for type {type}")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"Failed to get stats: {str(e)}"
                }
            )
