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
from datetime import datetime

logger = get_logger(__name__)


class DownloadControllerJob:
    def __init__(self, context: DownloadContext):
        # self.ctx = context
        self.orchestrator = context.orchestrator

    async def list_jobs(self, **kwargs) -> APIResponse:
        """List all download jobs."""
        try:
            jobs_data = await self.orchestrator.list_download_jobs_dict()

            return APIResponse(
                status=200,
                body={
                    "code": 200,
                    "message": "Jobs retrieved successfully",
                    "data": {
                        "jobs": jobs_data,
                        "count": len(jobs_data)
                    }
                }
            )

        except Exception as e:
            logger.exception(f"Failed to list jobs")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"Failed to list jobs: {str(e)}"
                }
            )

    async def create_job(self,
                         job_name: str,
                         job_type: str,
                         source_type: str,
                         source_id: str,
                         storage_path: str,
                         source_name: Optional[str] = None,
                         source_owner_id: Optional[str] = None,
                         target_quality: str = "lossless",
                         embed_cover: bool = True,
                         embed_lyrics: bool = True,
                         embed_metadata: bool = True,
                         **kwargs) -> APIResponse:
        """
        Create a new download job.

        Args:
            job_name: Human-readable job name
            job_type: Job type ('playlist', 'album', 'artist', 'manual')
            source_type: Source type ('playlist', 'album', 'artist')
            source_id: Source ID (playlist ID, album ID, etc.)
            storage_path: Storage directory path
            source_name: Optional source name
            source_owner_id: Source owner ID
            target_quality: Target audio quality
            embed_cover: Whether to download cover art
            embed_lyrics: Whether to download lyrics
            embed_metadata: Whether to embed metadata
        """
        try:
            job_id = await self.orchestrator.create_download_job(
                job_name=job_name,
                job_type=job_type,
                source_type=source_type,
                source_id=source_id,
                storage_path=storage_path,
                source_name=source_name,
                source_owner_id=source_owner_id,
                target_quality=target_quality,
                embed_cover=embed_cover,
                embed_lyrics=embed_lyrics,
                embed_metadata=embed_metadata
            )

            # 在session内获取job数据，避免detached instance问题
            job_data = await self.orchestrator.get_download_job_dict(job_id)

            return APIResponse(
                status=201,
                body={
                    "code": 201,
                    "message": "Download job created successfully",
                    "data": job_data or {"job_id": job_id}
                }
            )

        except Exception as e:
            logger.exception(f"Failed to create download job")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"Failed to create job: {str(e)}"
                }
            )

    async def retry_job_tasks(self, job_id: int, **kwargs) -> APIResponse:
        """Restart all failed tasks in a job."""
        try:
            job_id = int(job_id)
            restarted_task_ids = await self.orchestrator.restart_failed_tasks(job_id)

            return APIResponse(
                status=200,
                body={
                    "code": 200,
                    "message": f"Restarted {len(restarted_task_ids)} failed tasks",
                    "data": {
                        "job_id": job_id,
                        "restarted_count": len(restarted_task_ids),
                        "restarted_task_ids": restarted_task_ids
                    }
                }
            )
        except Exception as e:
            logger.exception(f"Failed to restart failed tasks")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"Failed to restart failed tasks: {str(e)}"
                }
            )

    async def update_job(self,
                         job_id: int,
                         job_name: Optional[str] = None,
                         storage_path: Optional[str] = None,
                         filename_template: Optional[str] = None,
                         target_quality: Optional[str] = None,
                         embed_cover: Optional[bool] = None,
                         embed_lyrics: Optional[bool] = None,
                         embed_metadata: Optional[bool] = None,
                         enabled: Optional[bool] = None,
                         **kwargs) -> APIResponse:
        try:
            job_id = int(job_id)

            update_fields: Dict[str, Any] = {"updated_at": datetime.utcnow()}
            if job_name is not None:
                update_fields["job_name"] = job_name
            if storage_path is not None:
                update_fields["storage_path"] = storage_path
            if filename_template is not None:
                update_fields["filename_template"] = filename_template
            if target_quality is not None:
                update_fields["target_quality"] = target_quality
            if embed_cover is not None:
                update_fields["embed_cover"] = bool(embed_cover)
            if embed_lyrics is not None:
                update_fields["embed_lyrics"] = bool(embed_lyrics)
            if embed_metadata is not None:
                update_fields["embed_metadata"] = bool(embed_metadata)
            if enabled is not None:
                update_fields["enabled"] = bool(enabled)

            if "storage_path" in update_fields and not str(update_fields["storage_path"]).strip():
                return APIResponse(
                    status=400,
                    body={"code": 400, "message": "storage_path 不能为空"}
                )
            if "filename_template" in update_fields and not str(update_fields["filename_template"]).strip():
                return APIResponse(
                    status=400,
                    body={"code": 400, "message": "filename_template 不能为空"}
                )

            job_data = await self.orchestrator.update_download_job_dict(job_id, **update_fields)
            if not job_data:
                return APIResponse(
                    status=404,
                    body={"code": 404, "message": f"Job not found: {job_id}"}
                )

            return APIResponse(
                status=200,
                body={
                    "code": 200,
                    "message": "Job updated successfully",
                    "data": job_data
                }
            )
        except Exception as e:
            logger.exception("Failed to update job")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"Failed to update job: {str(e)}"
                }
            )

    async def delete_job(self, job_id: int, **kwargs) -> APIResponse:
        try:
            job_id = int(job_id)
            result = await self.orchestrator.delete_download_job(job_id)
            if result:
                return APIResponse(
                    status=200,
                    body={
                        "code": 200,
                        "message": f"Job {job_id} deleted successfully"
                    }
                )
            else:
                return APIResponse(
                    status=404,
                    body={"code": 404, "message": f"Job not found: {job_id}"}
                )
        except Exception as e:
            logger.exception("Failed to delete job")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"Failed to delete job: {str(e)}"
                }
            )
