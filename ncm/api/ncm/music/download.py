"""Music download controller with new task-driven architecture."""

import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path

from ncm.service.download.orchestrator import DownloadOrchestrator, DownloadProcess
from ncm.infrastructure.db.models.download_task import DownloadTask, TaskProgress
from ncm.infrastructure.db.models.download_job import DownloadJob
from ncm.core.options import APIResponse
from ncm.core.logging import get_logger
from ncm.infrastructure.http import ncm_service

logger = get_logger(__name__)


class DownloadController:
    """HTTP controller for music download functionality with job management."""

    def __init__(self):
        """Initialize download controller."""
        self.orchestrator = DownloadOrchestrator(
            downloads_dir="downloads",
            max_concurrent_downloads=3,
            max_threads_per_download=4
        )
        self.process = DownloadProcess(self.orchestrator)

        from ncm.service.download.orchestrator.scheduler import ProcessScheduler
        self._scheduler = ProcessScheduler(self.process)
        self._scheduler.start_scheduler()

    # ===== JOB MANAGEMENT =====

    @ncm_service("/ncm/download/job/create", ["GET", "POST"])
    async def create_job(self,
                         job_name: str,
                         job_type: str,
                         source_type: str,
                         source_id: str,
                         storage_path: str,
                         source_name: Optional[str] = None,
                         target_quality: str = "lossless",
                         download_cover: bool = True,
                         download_lyrics: bool = True,
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
            target_quality: Target audio quality
            download_cover: Whether to download cover art
            download_lyrics: Whether to download lyrics
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
                target_quality=target_quality,
                download_cover=download_cover,
                download_lyrics=download_lyrics,
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

    @ncm_service("/ncm/download/job/list", ["GET"])
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

    @ncm_service("/ncm/download/job/process/run", ["GET", "POST"])
    async def job_process(self, **kwargs) -> APIResponse:
        """start process for a job."""
        try:
            results = await self.process.run()

            return APIResponse(
                status=202,
                body={
                    "code": 202,
                    "message": f"Submitted {results['submitted_tasks']} tasks",
                    "data": {
                        **results
                    }
                }
            )

        except Exception as e:
            logger.exception(f"Failed to run for job process")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"Failed to run for job process: {str(e)}"
                }
            )

    @ncm_service("/ncm/download/job/process/start", ["GET", "POST"])
    async def job_process_start(self, batch_size: int = 10, **kwargs) -> APIResponse:
        try:
            started = await self.process.start(batch_size=batch_size)
            status = self.process.get_status()
            return APIResponse(
                status=202 if started else 200,
                body={
                    "code": 202 if started else 200,
                    "message": "Process started" if started else "Process already running",
                    "data": status
                }
            )
        except Exception as e:
            logger.exception("Failed to start job process")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"Failed to start: {str(e)}"
                }
            )

    @ncm_service("/ncm/download/job/process/status", ["GET"])
    async def job_process_status(self, **kwargs) -> APIResponse:
        try:
            status = self.process.get_status()
            return APIResponse(
                status=200,
                body={
                    "code": 200,
                    "message": "Process status",
                    "data": status
                }
            )
        except Exception as e:
            logger.exception("Failed to get process status")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"Failed to get status: {str(e)}"
                }
            )

    @ncm_service("/ncm/download/scheduler/set_cron", ["POST"])
    async def scheduler_set_cron(self, cron_expr: str, batch_size: int = 10, **kwargs) -> APIResponse:
        try:
            ok = self._scheduler.set_cron(cron_expr, batch_size=batch_size)
            return APIResponse(
                status=200,
                body={
                    "code": 200,
                    "message": "Cron set" if ok else "Failed to set cron",
                    "data": {
                        "cron": cron_expr,
                        "batch_size": batch_size,
                        "next_run_time": self._scheduler.next_run_time()
                    }
                }
            )
        except Exception as e:
            logger.exception("Failed to set scheduler cron")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"Failed to set cron: {str(e)}"
                }
            )

    @ncm_service("/ncm/download/scheduler/start", ["GET", "POST"])
    async def scheduler_start(self, **kwargs) -> APIResponse:
        try:
            ok = self._scheduler.enable()
            return APIResponse(
                status=200 if ok else 400,
                body={
                    "code": 200 if ok else 400,
                    "message": "Schedule enabled" if ok else "Cron not set",
                    "data": {
                        "next_run_time": self._scheduler.next_run_time()
                    }
                }
            )
        except Exception as e:
            logger.exception("Failed to start scheduler")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"Failed to start scheduler: {str(e)}"
                }
            )

    @ncm_service("/ncm/download/scheduler/stop", ["GET", "POST"])
    async def scheduler_stop(self, **kwargs) -> APIResponse:
        try:
            ok = self._scheduler.disable()
            return APIResponse(
                status=200,
                body={
                    "code": 200,
                    "message": "Schedule disabled" if ok else "No schedule",
                    "data": {
                        "next_run_time": self._scheduler.next_run_time()
                    }
                }
            )
        except Exception as e:
            logger.exception("Failed to stop scheduler")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"Failed to stop scheduler: {str(e)}"
                }
            )

    @ncm_service("/ncm/download/scheduler/next_run", ["GET"])
    async def scheduler_next_run(self, **kwargs) -> APIResponse:
        try:
            next_run = self._scheduler.next_run_time()
            return APIResponse(
                status=200,
                body={
                    "code": 200,
                    "message": "Next run time",
                    "data": {
                        "next_run_time": next_run
                    }
                }
            )
        except Exception as e:
            logger.exception("Failed to get next run time")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"Failed to get next run time: {str(e)}"
                }
            )
    async def cleanup(self):
        try:
            if hasattr(self, "_scheduler") and self._scheduler:
                await self._scheduler.cleanup()
        except Exception:
            pass
        await self.orchestrator.close()

    @ncm_service("/ncm/download/job/submit_batch", ["POST"])
    async def submit_job_batch(self, job_id: int, music_ids: List[str], **kwargs) -> APIResponse:
        """Submit batch download tasks for a job."""
        try:
            job_id = int(job_id)
            task_ids = await self.orchestrator.submit_batch_download(job_id, music_ids)

            return APIResponse(
                status=202,
                body={
                    "code": 202,
                    "message": f"Submitted {len(task_ids)} tasks for job {job_id}",
                    "data": {
                        "job_id": job_id,
                        "submitted_tasks": len(task_ids),
                        "task_ids": task_ids
                    }
                }
            )

        except Exception as e:
            logger.exception(f"Failed to submit batch for job {job_id}")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"Failed to submit batch: {str(e)}"
                }
            )

    # ===== TASK MANAGEMENT =====

    @ncm_service("/ncm/download/task/submit", ["GET", "POST"])
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

    @ncm_service("/ncm/download/task/status", ["GET"])
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

    @ncm_service("/ncm/download/task/wait", ["GET"])
    async def wait_for_task(self, task_id: int, **kwargs) -> APIResponse:
        """Wait for task completion."""
        try:
            task_id = int(task_id)
            task_data = await self.orchestrator.wait_for_task_dict(task_id)

            if not task_data:
                return APIResponse(
                    status=404,
                    body={
                        "code": 404,
                        "message": "Task not found"
                    }
                )

            progress_flags = task_data.get('progress_flags', 0)
            progress_summary = TaskProgress.get_progress_summary(progress_flags)

            if task_data.get('status') == "completed":
                return APIResponse(
                    status=200,
                    body={
                        "code": 200,
                        "message": "Task completed successfully",
                        "data": {
                            **task_data,
                            "progress_summary": progress_summary
                        }
                    }
                )
            else:
                return APIResponse(
                    status=400,
                    body={
                        "code": 400,
                        "message": f"Task failed: {task_data.get('error_message', 'Unknown error')}",
                        "data": {
                            **task_data,
                            "progress_summary": progress_summary
                        }
                    }
                )

        except Exception as e:
            logger.exception(f"Failed to wait for task")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"Failed to wait for task: {str(e)}"
                }
            )

    @ncm_service("/ncm/download/task/cancel", ["POST"])
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

    # ===== QUALITY MANAGEMENT =====

    @ncm_service("/ncm/download/task/upgrade_quality", ["GET", "POST"])
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

    @ncm_service("/ncm/download/job/restart_failed", ["GET", "POST"])
    async def restart_failed_tasks(self, job_id: int, **kwargs) -> APIResponse:
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

    # ===== SYSTEM STATUS =====

    @ncm_service("/ncm/download/status", ["GET"])
    async def get_system_status(self, **kwargs) -> APIResponse:
        """Get overall download system status."""
        try:
            stats = await self.orchestrator.get_stats()

            return APIResponse(
                status=200,
                body={
                    "code": 200,
                    "message": "System status retrieved successfully",
                    "data": stats
                }
            )

        except Exception as e:
            logger.exception(f"Failed to get system status")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"Failed to get system status: {str(e)}"
                }
            )

    @ncm_service("/ncm/download/tasks/active", ["GET"])
    async def list_active_tasks(self, **kwargs) -> APIResponse:
        """List currently active tasks."""
        try:
            active_tasks_data = await self.orchestrator.list_active_tasks_dict()

            return APIResponse(
                status=200,
                body={
                    "code": 200,
                    "message": "Active tasks retrieved successfully",
                    "data": {
                        "tasks": list(active_tasks_data.values()),
                        "count": len(active_tasks_data)
                    }
                }
            )

        except Exception as e:
            logger.exception(f"Failed to list active tasks")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"Failed to list active tasks: {str(e)}"
                }
            )

    # ===== LEGACY COMPATIBILITY (SIMPLIFIED) =====

    @ncm_service("/ncm/music/download/add", ["GET", "POST"])
    async def legacy_add_download(self,
                                  music_id: str,
                                  storage_location_id: int,
                                  quality: str = "lossless",
                                  **kwargs) -> APIResponse:
        """
        Legacy endpoint: Add download with automatic job creation.
        Creates a temporary job if storage_location_id doesn't exist as job.
        """
        try:
            # Try to find existing job by storage_location_id (legacy compatibility)
            jobs = await self.orchestrator.list_download_jobs()
            job = None
            for j in jobs:
                if j.id == int(storage_location_id):
                    job = j
                    break

            # Create temporary job if not found
            if not job:
                job_id = await self.orchestrator.create_download_job(
                    job_name=f"Legacy Job {storage_location_id}",
                    job_type="manual",
                    source_type="manual",
                    source_id=str(storage_location_id),
                    storage_path=f"downloads/legacy/{storage_location_id}",
                    target_quality=quality
                )
            else:
                job_id = job.id

            # Submit task and wait for completion (legacy behavior)
            task_id = await self.orchestrator.submit_download(music_id, int(job_id), quality)
            result = await self.orchestrator.wait_for_task(task_id)

            if result and result.status == "completed":
                return APIResponse(
                    status=200,
                    body={
                        "code": 200,
                        "message": "Download completed successfully",
                        "data": {
                            "music_id": result.music_id,
                            "title": result.music_title,
                            "artist": result.music_artist,
                            "file_format": result.file_format,
                            "file_size": result.file_size,
                            "file_path": result.file_path,
                            "quality": result.quality
                        }
                    }
                )
            else:
                return APIResponse(
                    status=400,
                    body={
                        "code": 400,
                        "message": f"Download failed: {result.error_message if result else 'Unknown error'}"
                    }
                )

        except Exception as e:
            logger.exception(f"Legacy download failed")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"Download failed: {str(e)}"
                }
            )

    @ncm_service("/ncm/music/download/submit", ["GET", "POST"])
    async def legacy_submit_download(self,
                                     music_id: str,
                                     storage_location_id: int,
                                     quality: str = "lossless",
                                     **kwargs) -> APIResponse:
        """Legacy endpoint: Submit download (non-blocking)."""
        try:
            # Find or create job (same logic as legacy_add_download)
            jobs = await self.orchestrator.list_download_jobs()
            job = None
            for j in jobs:
                if j.id == int(storage_location_id):
                    job = j
                    break

            if not job:
                job_id = await self.orchestrator.create_download_job(
                    job_name=f"Legacy Job {storage_location_id}",
                    job_type="manual",
                    source_type="manual",
                    source_id=str(storage_location_id),
                    storage_path=f"downloads/legacy/{storage_location_id}",
                    target_quality=quality
                )
            else:
                job_id = job.id

            task_id = await self.orchestrator.submit_download(music_id, int(job_id), quality)

            return APIResponse(
                status=202,
                body={
                    "code": 202,
                    "message": "Download task submitted successfully",
                    "data": {
                        "task_id": task_id,
                        "music_id": music_id,
                        "job_id": job_id,
                        "quality": quality
                    }
                }
            )

        except Exception as e:
            logger.exception(f"Legacy submit failed")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"Failed to submit download: {str(e)}"
                }
            )

    # removed duplicate cleanup at end of class; unified earlier cleanup handles scheduler and orchestrator
