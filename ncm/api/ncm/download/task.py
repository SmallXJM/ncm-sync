"""Music download controller with new task-driven architecture."""

import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path

from ncm.api.ncm.download import DownloadContext
from ncm.service.download.orchestrator import DownloadOrchestrator, DownloadProcess
from ncm.infrastructure.db.models.download_task import DownloadTask, TaskProgress
from ncm.infrastructure.db.models.download_job import DownloadJob
from ncm.core.options import APIResponse
from ncm.core.logging import get_logger
from ncm.infrastructure.http import ncm_service
from ncm.infrastructure.config import get_config_manager

logger = get_logger(__name__)


class DownloadControllerTask:
    def __init__(self, context: DownloadContext):
        # self.ctx = context
        self.orchestrator = context.orchestrator

    # ===== TASK MANAGEMENT =====

    async def submit_task(self,
                          music_id: str,
                          job_id: int,
                          target_quality: Optional[str] = None,
                          **kwargs) -> APIResponse:
        """
        Submit a single download task.

        Args:
            music_id: Music ID to download
            job_id: Job ID for organization
            target_quality: Override job's target quality (optional)
        """
        try:
            # Use job's target quality if not specified
            if target_quality is None:
                job = await self.orchestrator.get_download_job(int(job_id))
                if not job:
                    return APIResponse(
                        status=404,
                        body={
                            "code": 404,
                            "message": "Job not found"
                        }
                    )
                target_quality = job.target_quality

            task_id = await self.orchestrator.submit_download(music_id, int(job_id), target_quality)

            return APIResponse(
                status=202,
                body={
                    "code": 202,
                    "message": "Task submitted successfully",
                    "data": {
                        "task_id": task_id,
                        "music_id": music_id,
                        "job_id": job_id,
                        "target_quality": target_quality,
                        "status": "pending"
                    }
                }
            )

        except Exception as e:
            logger.exception(f"Failed to submit task for music {music_id}")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"Failed to submit task: {str(e)}"
                }
            )

    async def get_task_status(self, task_id: int, **kwargs) -> APIResponse:
        """Get task status and progress."""
        try:
            task_id = int(task_id)
            task_data = await self.orchestrator.get_task_dict(task_id)

            if not task_data:
                return APIResponse(
                    status=404,
                    body={
                        "code": 404,
                        "message": "Task not found"
                    }
                )

            # Get progress summary from task data
            progress_flags = task_data.get('progress_flags', 0)
            progress_summary = TaskProgress.get_progress_summary(progress_flags)

            return APIResponse(
                status=200,
                body={
                    "code": 200,
                    "message": "Task status retrieved successfully",
                    "data": {
                        **task_data,
                        "progress_summary": progress_summary
                    }
                }
            )

        except Exception as e:
            logger.exception(f"Failed to get task status")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"Failed to get task status: {str(e)}"
                }
            )

    async def cancel_task(self, task_id: int, **kwargs) -> APIResponse:
        """Cancel a task."""
        try:
            task_id = int(task_id)
            success = await self.orchestrator.cancel_task(task_id)

            if success:
                return APIResponse(
                    status=200,
                    body={
                        "code": 200,
                        "message": "Task cancelled successfully"
                    }
                )
            else:
                return APIResponse(
                    status=404,
                    body={
                        "code": 404,
                        "message": "Task not found or already completed"
                    }
                )

        except Exception as e:
            logger.exception(f"Failed to cancel task")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"Failed to cancel task: {str(e)}"
                }
            )

    async def reset_task(self, task_id: int, **kwargs) -> APIResponse:
        """Reset a task to pending status."""
        try:
            task_id = int(task_id)
            success = await self.orchestrator.reset_task(task_id)

            if success:
                return APIResponse(
                    status=200,
                    body={
                        "code": 200,
                        "message": "Task reset successfully"
                    }
                )
            else:
                return APIResponse(
                    status=404,
                    body={
                        "code": 404,
                        "message": "Task not found"
                    }
                )
        except Exception as e:
            logger.exception(f"Failed to reset task")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"Failed to reset task: {str(e)}"
                }
            )

    async def list_tasks(self,
                        page: int = 1,
                        limit: int = 20,
                        job_id: Optional[int] = None,
                        status: Optional[str] = None,
                        keyword: Optional[str] = None,
                        **kwargs) -> APIResponse:
        """List tasks with pagination and filtering."""
        try:
            page = int(page)
            limit = int(limit)
            offset = (page - 1) * limit
            if job_id:
                job_id = int(job_id)

            result = await self.orchestrator.search_tasks(
                job_id=job_id,
                status=status,
                keyword=keyword,
                limit=limit,
                offset=offset
            )

            return APIResponse(
                status=200,
                body={
                    "code": 200,
                    "message": "Tasks retrieved successfully",
                    "data": result
                }
            )
        except Exception as e:
            logger.exception(f"Failed to list tasks")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"Failed to list tasks: {str(e)}"
                }
            )

    # ===== QUALITY MANAGEMENT =====

    async def upgrade_task_quality(self,
                                   job_id: int,
                                   music_id: str,
                                   new_target_quality: str,
                                   **kwargs) -> APIResponse:
        """Upgrade task quality by restarting the task."""
        try:
            job_id = int(job_id)
            new_task_id = await self.orchestrator.upgrade_task_quality(
                job_id, music_id, new_target_quality
            )

            return APIResponse(
                status=202,
                body={
                    "code": 202,
                    "message": "Quality upgrade initiated",
                    "data": {
                        "new_task_id": new_task_id,
                        "job_id": job_id,
                        "music_id": music_id,
                        "new_target_quality": new_target_quality
                    }
                }
            )

        except Exception as e:
            logger.exception(f"Failed to upgrade quality")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"Failed to upgrade quality: {str(e)}"
                }
            )
