"""Core audio downloader implementation."""

import asyncio
import hashlib
import time
from pathlib import Path
from typing import Optional, Callable, Dict, Any
import httpx
from datetime import datetime

from .download_task import DownloadTask, TaskStatus, DownloadSegment
from .progress_tracker import ProgressTracker
from ncm.core.logging import get_logger

logger = get_logger(__name__)


class AudioDownloader:
    """Core audio downloader with multi-threading and resume support."""
    
    def __init__(self, 
                 max_concurrent_downloads: int = 3,
                 max_threads_per_download: int = 4,
                 chunk_size: int = 4 * 1024 * 1024,
                 timeout: int = 30,
                 retry_attempts: int = 3):
        """
        Initialize audio downloader.
        
        Args:
            max_concurrent_downloads: Maximum concurrent downloads
            max_threads_per_download: Maximum threads per download
            chunk_size: Download chunk size in bytes
            timeout: HTTP timeout in seconds
            retry_attempts: Number of retry attempts for failed requests
        """
        self.max_concurrent_downloads = max_concurrent_downloads
        self.max_threads_per_download = max_threads_per_download
        self.chunk_size = chunk_size
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        
        self.progress_tracker = ProgressTracker()
        self._active_downloads: Dict[str, DownloadTask] = {}
        self._download_semaphore = asyncio.Semaphore(max_concurrent_downloads)
        
        # HTTP client with HTTP/2 support
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            http2=True,
            follow_redirects=True
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Close the downloader and cleanup resources."""
        await self._client.aclose()
    
    async def download(self, 
                      task: DownloadTask,
                      progress_callback: Optional[Callable[[DownloadTask], None]] = None) -> bool:
        """
        Download a single file with multi-threading and resume support.
        
        Args:
            task: Download task
            progress_callback: Progress update callback
            
        Returns:
            True if download successful, False otherwise
        """
        async with self._download_semaphore:
            return await self._download_task(task, progress_callback)
    
    async def _download_task(self, 
                           task: DownloadTask,
                           progress_callback: Optional[Callable[[DownloadTask], None]] = None) -> bool:
        """Internal download implementation."""
        try:
            task.status = TaskStatus.DOWNLOADING
            task.started_at = datetime.now()
            self._active_downloads[task.music_id] = task
            self.progress_tracker.start_task(task.music_id)
            
            logger.info(f"Starting download: {task.music_id}")
            
            # Check if we can resume
            if await self._can_resume_download(task):
                logger.info(f"Resuming download: {task.music_id}")
            else:
                # Start fresh download
                await self._prepare_fresh_download(task)
            
            # Download segments concurrently
            success = await self._download_segments(task, progress_callback)
            
            # Handle URL expiration case
            if task.status == TaskStatus.URL_EXPIRED:
                logger.info(f"Download paused due to URL expiration: {task.music_id}. Progress saved for resume.")
                # Don't cleanup temp files, keep them for resume
                task.save_resume_info()
                self.progress_tracker.finish_task(task.music_id)
                self._active_downloads.pop(task.music_id, None)
                
                if progress_callback:
                    progress_callback(task)
                
                return False  # Return false but don't mark as failed
            
            if success:
                # Merge segments and verify
                success = await self._finalize_download(task)
            
            if success:
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                logger.info(f"Download completed: {task.music_id}")
            else:
                task.status = TaskStatus.FAILED
                logger.error(f"Download failed: {task.music_id}")
            
            # Cleanup
            if success:
                task.cleanup_temp_files()
            else:
                task.save_resume_info()
            
            self.progress_tracker.finish_task(task.music_id)
            self._active_downloads.pop(task.music_id, None)
            
            if progress_callback:
                progress_callback(task)
            
            return success
            
        except Exception as e:
            logger.exception(f"Download error for {task.music_id}: {str(e)}")
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.save_resume_info()
            self._active_downloads.pop(task.music_id, None)
            
            if progress_callback:
                progress_callback(task)
            
            return False
    
    async def _can_resume_download(self, task: DownloadTask) -> bool:
        """Check if download can be resumed."""
        if not task.resume_file or not task.resume_file.exists():
            return False
        
        # Load existing task
        existing_task = DownloadTask.load_from_resume_file(task.resume_file)
        if not existing_task:
            return False
        
        # Check if segments exist and are valid
        valid_segments = 0
        for i, segment in enumerate(existing_task.segments):
            segment_file = existing_task.get_segment_file_path(i)
            if segment_file.exists() and segment_file.stat().st_size == segment.downloaded:
                valid_segments += 1
        
        if valid_segments > 0:
            # Copy resume data
            task.segments = existing_task.segments
            task.downloaded_bytes = existing_task.downloaded_bytes
            task.temp_dir = existing_task.temp_dir
            task.resume_file = existing_task.resume_file
            return True
        
        return False
    
    async def _prepare_fresh_download(self, task: DownloadTask):
        """Prepare for fresh download."""
        # Create segments
        task.create_segments()
        
        # Create temp directory
        task.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Save initial resume info
        task.save_resume_info()
    
    async def _download_segments(self, 
                               task: DownloadTask,
                               progress_callback: Optional[Callable[[DownloadTask], None]] = None) -> bool:
        """Download all segments concurrently."""
        # Create semaphore for this task's threads
        thread_semaphore = asyncio.Semaphore(task.max_threads)
        
        # Create download tasks for incomplete segments
        download_tasks = []
        for i, segment in enumerate(task.segments):
            if not segment.completed:
                download_tasks.append(
                    self._download_segment(task, i, thread_semaphore, progress_callback)
                )
        
        if not download_tasks:
            return True  # All segments already completed
        
        # Run segment downloads concurrently
        results = await asyncio.gather(*download_tasks, return_exceptions=True)
        
        # Check if URL expired during download
        if task.status == TaskStatus.URL_EXPIRED:
            logger.info(f"Download paused due to URL expiration: {task.music_id}")
            return False  # Don't mark as failed, just paused for URL refresh
        
        # Check results
        success = True
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Segment download error: {result}")
                success = False
            elif not result:
                success = False
        
        return success
    
    async def _download_segment(self, 
                              task: DownloadTask, 
                              segment_index: int,
                              semaphore: asyncio.Semaphore,
                              progress_callback: Optional[Callable[[DownloadTask], None]] = None) -> bool:
        """Download a single segment."""
        async with semaphore:
            segment = task.segments[segment_index]
            segment_file = task.get_segment_file_path(segment_index)
            
            # Check if segment already exists and is complete
            if segment_file.exists():
                existing_size = segment_file.stat().st_size
                if existing_size == segment.size:
                    segment.downloaded = segment.size
                    segment.completed = True
                    return True
                elif existing_size > 0:
                    # Partial download exists
                    segment.downloaded = existing_size
            
            # Calculate range to download
            start_byte = segment.start + segment.downloaded
            end_byte = segment.end
            
            if start_byte > end_byte:
                segment.completed = True
                return True
            
            # Download with retry logic
            for attempt in range(self.retry_attempts):
                try:
                    # Make HTTP request with range header
                    headers = {
                        'Range': f'bytes={start_byte}-{end_byte}',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    
                    async with self._client.stream('GET', task.url, headers=headers) as response:
                        # Check for URL expiration (403 Forbidden)
                        if response.status_code == 403:
                            logger.warning(f"URL expired (HTTP 403) for {task.music_id}, marking task for URL refresh")
                            # Mark task as URL expired and save progress
                            task.status = TaskStatus.URL_EXPIRED
                            task.error_message = "Download URL has expired"
                            task.save_resume_info()
                            return False  # Stop this segment download
                        
                        if response.status_code not in [200, 206]:
                            raise httpx.HTTPStatusError(
                                f"HTTP {response.status_code}", 
                                request=response.request, 
                                response=response
                            )
                        
                        # Open segment file for writing
                        with open(segment_file, 'ab') as f:
                            async for chunk in response.aiter_bytes(chunk_size=8192):
                                f.write(chunk)
                                segment.downloaded += len(chunk)
                                
                                # Update progress
                                task.update_downloaded_bytes()
                                self.progress_tracker.update_task_progress(task.music_id, task.downloaded_bytes)
                                
                                # Call progress callback periodically
                                if progress_callback and int(time.time()) % 2 == 0:
                                    progress_callback(task)
                                
                                # Save resume info periodically
                                if segment.downloaded % (1024 * 1024) == 0:  # Every 1MB
                                    task.save_resume_info()
                    
                    # Mark segment as completed
                    segment.completed = True
                    task.save_resume_info()
                    
                    logger.debug(f"Segment {segment_index} completed for {task.music_id}")
                    return True
                    
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 403:
                        logger.warning(f"URL expired (HTTP 403) for {task.music_id}, marking task for URL refresh")
                        # Mark task as URL expired and save progress
                        task.status = TaskStatus.URL_EXPIRED
                        task.error_message = "Download URL has expired"
                        task.save_resume_info()
                        return False  # Stop this segment download
                    else:
                        logger.warning(f"Segment {segment_index} download attempt {attempt + 1} failed: {str(e)}")
                        if attempt == self.retry_attempts - 1:
                            logger.error(f"Segment {segment_index} download failed after {self.retry_attempts} attempts")
                            return False
                        
                        # Wait before retry
                        await asyncio.sleep(2 ** attempt)
                        
                except Exception as e:
                    logger.warning(f"Segment {segment_index} download attempt {attempt + 1} failed: {str(e)}")
                    if attempt == self.retry_attempts - 1:
                        logger.error(f"Segment {segment_index} download failed after {self.retry_attempts} attempts")
                        return False
                    
                    # Wait before retry
                    await asyncio.sleep(2 ** attempt)
            
            return False
    
    async def _finalize_download(self, task: DownloadTask) -> bool:
        """Merge segments and verify download."""
        try:
            # Ensure output directory exists
            task.file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Merge segments
            with open(task.file_path, 'wb') as output_file:
                for i, segment in enumerate(task.segments):
                    segment_file = task.get_segment_file_path(i)
                    if not segment_file.exists():
                        logger.error(f"Segment file missing: {segment_file}")
                        return False
                    
                    with open(segment_file, 'rb') as seg_file:
                        while True:
                            chunk = seg_file.read(8192)
                            if not chunk:
                                break
                            output_file.write(chunk)
            
            # Verify file size
            actual_size = task.file_path.stat().st_size
            if actual_size != task.file_size:
                logger.error(f"File size mismatch: expected {task.file_size}, got {actual_size}")
                return False
            
            # Verify MD5 hash
            if task.md5_hash:
                actual_md5 = await self._calculate_md5(task.file_path)
                if actual_md5.lower() != task.md5_hash.lower():
                    logger.error(f"MD5 hash mismatch: expected {task.md5_hash}, got {actual_md5}")
                    return False
            
            logger.info(f"Download verified successfully: {task.music_id}")
            return True
            
        except Exception as e:
            logger.error(f"Download finalization failed: {str(e)}")
            return False
    
    async def _calculate_md5(self, file_path: Path) -> str:
        """Calculate MD5 hash of a file."""
        hash_md5 = hashlib.md5()
        
        def _read_file():
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    hash_md5.update(chunk)
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _read_file)
        
        return hash_md5.hexdigest()
    
    def get_active_downloads(self) -> Dict[str, DownloadTask]:
        """Get currently active downloads."""
        return self._active_downloads.copy()
    
    def get_download_stats(self) -> Dict[str, Any]:
        """Get comprehensive download statistics."""
        return {
            "active_downloads": len(self._active_downloads),
            "global_stats": self.progress_tracker.get_global_stats(),
            "tasks": {
                task_id: {
                    "task": task.to_dict(),
                    "stats": self.progress_tracker.get_task_stats(task_id)
                }
                for task_id, task in self._active_downloads.items()
            }
        }