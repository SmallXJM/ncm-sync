"""Download manager for handling multiple downloads and queues."""

import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime

from .download_task import DownloadTask, TaskStatus
from .downloader import AudioDownloader
from ncm.core.logging import get_logger

logger = get_logger(__name__)


class DownloadManager:
    """Manages download queue and coordinates multiple downloads."""

    def __init__(self,
                 downloads_dir: str = "downloads",
                 max_concurrent_downloads: int = 3,
                 max_threads_per_download: int = 4,
                 auto_start: bool = True):
        """
        Initialize download manager.
        
        Args:
            downloads_dir: Base downloads directory
            max_concurrent_downloads: Maximum concurrent downloads
            max_threads_per_download: Maximum threads per download
            auto_start: Automatically start downloads when added
        """
        self.downloads_dir = Path(downloads_dir)
        self.downloads_dir.mkdir(parents=True, exist_ok=True)

        self.max_concurrent_downloads = max_concurrent_downloads
        self.max_threads_per_download = max_threads_per_download
        self.auto_start = auto_start

        # Initialize downloader
        self.downloader = AudioDownloader(
            max_concurrent_downloads=max_concurrent_downloads,
            max_threads_per_download=max_threads_per_download
        )

        # Task management
        self._tasks: Dict[str, DownloadTask] = {}
        self._queue: List[str] = []  # Task IDs in queue order
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._paused_tasks: set = set()

        # Callbacks
        self._progress_callbacks: List[Callable[[DownloadTask], None]] = []
        self._completion_callbacks: List[Callable[[DownloadTask, bool], None]] = []

        # Load existing tasks
        self._load_existing_tasks()

    def add_progress_callback(self, callback: Callable[[DownloadTask], None]):
        """Add progress update callback."""
        self._progress_callbacks.append(callback)

    def add_completion_callback(self, callback: Callable[[DownloadTask, bool], None]):
        """Add download completion callback."""
        self._completion_callbacks.append(callback)

    def add_download(self, task: DownloadTask) -> bool:
        """
        Add download task to queue.
        
        Args:
            task: Download task to add
            
        Returns:
            True if added successfully, False if already exists
        """
        # Check if task with same MD5 already exists (for resume)
        existing_task = self._find_task_by_md5(task.md5_hash)
        if existing_task:
            if existing_task.status == TaskStatus.URL_EXPIRED:
                # Update URL and resume download
                logger.info(f"Found expired task with same MD5, updating URL and resuming: {task.music_id}")
                existing_task.url = task.url
                existing_task.status = TaskStatus.PENDING
                existing_task.error_message = None

                # Add back to queue if not already there
                if existing_task.music_id not in self._queue:
                    self._queue.append(existing_task.music_id)

                if self.auto_start:
                    asyncio.create_task(self._process_queue())

                return True
            elif existing_task.status in [TaskStatus.COMPLETED, TaskStatus.DOWNLOADING]:
                logger.warning(f"Task with same MD5 already exists: {existing_task.music_id}")
                return False

        # Check if task with same music_id already exists
        if task.music_id in self._tasks:
            logger.warning(f"Task already exists: {task.music_id}")
            return False

        self._tasks[task.music_id] = task
        self._queue.append(task.music_id)

        logger.info(f"Added download task: {task.music_id}")

        if self.auto_start:
            asyncio.create_task(self._process_queue())

        return True

    def _find_task_by_md5(self, md5_hash: str) -> Optional[DownloadTask]:
        """Find task by MD5 hash."""
        for task in self._tasks.values():
            if task.md5_hash == md5_hash:
                return task
        return None

    def add_downloads_batch(self, tasks: List[DownloadTask]) -> int:
        """
        Add multiple download tasks.
        
        Args:
            tasks: List of download tasks
            
        Returns:
            Number of tasks successfully added
        """
        added_count = 0
        for task in tasks:
            if self.add_download(task):
                added_count += 1

        return added_count

    async def start_downloads(self):
        """Start processing download queue."""
        await self._process_queue()

    async def pause_download(self, task_id: str) -> bool:
        """
        Pause a download.
        
        Args:
            task_id: Task ID to pause
            
        Returns:
            True if paused successfully
        """
        if task_id not in self._tasks:
            return False

        task = self._tasks[task_id]
        if task.status == TaskStatus.DOWNLOADING:
            self._paused_tasks.add(task_id)
            task.status = TaskStatus.PAUSED

            # Cancel active download task
            if task_id in self._active_tasks:
                self._active_tasks[task_id].cancel()
                del self._active_tasks[task_id]

            task.save_resume_info()
            logger.info(f"Paused download: {task.music_id}")
            return True

        return False

    async def resume_download(self, task_id: str) -> bool:
        """
        Resume a paused download.
        
        Args:
            task_id: Task ID to resume
            
        Returns:
            True if resumed successfully
        """
        if task_id not in self._tasks or task_id not in self._paused_tasks:
            return False

        task = self._tasks[task_id]
        if task.status == TaskStatus.PAUSED:
            self._paused_tasks.remove(task_id)
            task.status = TaskStatus.PENDING

            # Add back to queue if not already there
            if task_id not in self._queue:
                self._queue.append(task_id)

            logger.info(f"Resumed download: {task.music_id}")

            # Process queue
            asyncio.create_task(self._process_queue())
            return True

        return False

    async def cancel_download(self, task_id: str) -> bool:
        """
        Cancel a download.
        
        Args:
            task_id: Task ID to cancel
            
        Returns:
            True if cancelled successfully
        """
        if task_id not in self._tasks:
            return False

        task = self._tasks[task_id]

        # Cancel active download
        if task_id in self._active_tasks:
            self._active_tasks[task_id].cancel()
            del self._active_tasks[task_id]

        # Remove from queue
        if task_id in self._queue:
            self._queue.remove(task_id)

        # Remove from paused tasks
        self._paused_tasks.discard(task_id)

        # Update task status
        task.status = TaskStatus.CANCELLED
        task.save_resume_info()

        logger.info(f"Cancelled download: {task.music_id}")
        return True

    async def remove_download(self, task_id: str, delete_files: bool = False) -> bool:
        """
        Remove download task.
        
        Args:
            task_id: Task ID to remove
            delete_files: Whether to delete downloaded files
            
        Returns:
            True if removed successfully
        """
        if task_id not in self._tasks:
            return False

        task = self._tasks[task_id]

        # Cancel if active
        await self.cancel_download(task_id)

        # Delete files if requested
        if delete_files:
            if task.file_path.exists():
                task.file_path.unlink()
            task.cleanup_temp_files()

        # Remove from tasks
        del self._tasks[task_id]

        logger.info(f"Removed download task: {task.music_id}")
        return True

    async def _process_queue(self):
        """Process download queue."""
        while self._queue:
            # Check if we have capacity for more downloads
            active_count = len(self._active_tasks)
            if active_count >= self.max_concurrent_downloads:
                break

            # Get next task from queue
            task_id = None
            for tid in self._queue[:]:
                if tid not in self._active_tasks and tid not in self._paused_tasks:
                    task_id = tid
                    break

            if not task_id:
                break

            # Remove from queue and start download
            self._queue.remove(task_id)
            task = self._tasks[task_id]

            # Skip if already completed
            if task.status == TaskStatus.COMPLETED:
                continue

            # Start download
            download_task = asyncio.create_task(
                self._download_with_callbacks(task)
            )
            self._active_tasks[task_id] = download_task

    async def _download_with_callbacks(self, task: DownloadTask):
        """Download with progress and completion callbacks."""
        try:
            def progress_callback(updated_task: DownloadTask):
                for callback in self._progress_callbacks:
                    try:
                        callback(updated_task)
                    except Exception as e:
                        logger.error(f"Progress callback error: {e}")

            # Start download
            success = await self.downloader.download(
                task,
                progress_callback=progress_callback
            )

            # Call completion callbacks
            for callback in self._completion_callbacks:
                try:
                    callback(task, success)
                except Exception as e:
                    logger.error(f"Completion callback error: {e}")

            return success

        finally:
            # Remove from active tasks
            self._active_tasks.pop(task.music_id, None)

            # Continue processing queue
            asyncio.create_task(self._process_queue())

    def _load_existing_tasks(self):
        """Load existing tasks from resume files."""
        cache_dir = self.downloads_dir / ".cache"
        if not cache_dir.exists():
            return

        for task_dir in cache_dir.iterdir():
            if not task_dir.is_dir():
                continue

            resume_file = task_dir / "resume.json"
            if not resume_file.exists():
                continue

            task = DownloadTask.load_from_resume_file(resume_file)
            if task:
                self._tasks[task.music_id] = task

                # Add to queue if not completed or cancelled
                if task.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
                    # URL_EXPIRED tasks should not be auto-added to queue
                    # They will be resumed when a new task with same MD5 is submitted
                    if task.status != TaskStatus.URL_EXPIRED:
                        self._queue.append(task.music_id)

                    if task.status == TaskStatus.PAUSED:
                        self._paused_tasks.add(task.music_id)

                status_msg = "URL expired, waiting for refresh" if task.status == TaskStatus.URL_EXPIRED else task.status.value
                logger.info(f"Loaded existing task: {task.music_id} (Status: {status_msg})")

    def get_expired_tasks(self) -> List[DownloadTask]:
        """Get all tasks with expired URLs."""
        return [task for task in self._tasks.values() if task.status == TaskStatus.URL_EXPIRED]

    def get_all_tasks(self) -> List[DownloadTask]:
        """Get all download tasks."""
        return list(self._tasks.values())

    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        """Get specific download task."""
        return self._tasks.get(task_id)

    def get_queue_status(self) -> Dict[str, Any]:
        """Get download queue status."""
        tasks_by_status = {}
        for task in self._tasks.values():
            status = task.status.value
            if status not in tasks_by_status:
                tasks_by_status[status] = 0
            tasks_by_status[status] += 1

        return {
            "total_tasks": len(self._tasks),
            "queue_length": len(self._queue),
            "active_downloads": len(self._active_tasks),
            "paused_downloads": len(self._paused_tasks),
            "tasks_by_status": tasks_by_status,
            "global_stats": self.downloader.get_download_stats()["global_stats"]
        }

    async def close(self):
        """Close download manager and cleanup resources."""
        # Cancel all active downloads
        for task_id in list(self._active_tasks.keys()):
            await self.cancel_download(task_id)

        # Close downloader
        await self.downloader.close()

        logger.info("Download manager closed")
