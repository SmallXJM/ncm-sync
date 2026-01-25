"""Music download controller with new task-driven architecture."""

from ncm.server.routers.download import DownloadContext
from ncm.client import APIResponse
from ncm.core.logging import get_logger

logger = get_logger(__name__)


class DownloadControllerDaemon:
    def __init__(self, context: DownloadContext):
        # self.ctx = context
        self.orchestrator = context.orchestrator
        self._scheduler = context.scheduler
        self.process = context.process

    async def daemon_control(self, action: str, **kwargs) -> APIResponse:
        """
        Unified control endpoint.
        Args:
            action: 'start', 'stop', 'trigger_now', 'set_cron'
            cron_expr: (optional)
        """
        try:
            if action == 'start':
                self._scheduler.start_scheduler()
                ok = self._scheduler.enable()
                return APIResponse(
                    status=200 if ok else 400,
                    body={
                        "code": 200 if ok else 400,
                        "message": "Daemon started" if ok else "Cron not set; scheduler running",
                        "data": {
                            "next_run_time": self._scheduler.next_run_time()
                        }
                    }
                )
            elif action == 'stop':
                ok = self._scheduler.disable()
                return APIResponse(
                    status=200,
                    body={
                        "code": 200,
                        "message": "Daemon stopped" if ok else "Daemon was not running",
                        "data": {
                            "next_run_time": self._scheduler.next_run_time()
                        }
                    }
                )
            elif action == 'trigger_now':
                results = await self.process.start(self._scheduler._batch_size)
                return APIResponse(
                    status=202,
                    body={
                        "code": 202,
                        "message": f"Triggered run",
                        "data": {
                            "is_running": results
                        }
                    }
                )
            elif action == 'preview_cron':
                cron_expr = kwargs.get('cron_expr')
                if not cron_expr:
                    return APIResponse(status=400, body={"code": 400, "message": "Missing cron_expr"})
                
                next_run = self._scheduler.preview_next_run(cron_expr)
                return APIResponse(
                    status=200,
                    body={
                        "code": 200,
                        "message": "Preview calculated",
                        "data": {
                            "next_run_time": next_run
                        }
                    }
                )
        except Exception as e:
            logger.exception("Failed to control daemon")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"Failed to control daemon: {str(e)}"
                }
            )