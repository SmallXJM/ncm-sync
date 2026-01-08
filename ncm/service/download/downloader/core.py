"""Core audio downloader implementation for new task-driven architecture."""

import asyncio
import hashlib
import shutil
import time
from pathlib import Path
from typing import Optional

import httpx
from ncm.core.logging import get_logger
from ncm.service.download.service.async_task_service import AsyncTaskService
from ncm.service.download.models import get_task_cache_registry

logger = get_logger(__name__)


class AudioDownloader:
    """统一的音频下载器 - 支持分段下载和断点续传"""
    
    def __init__(self, downloads_dir: str = "downloads", max_concurrent: int = 3, max_threads: int = 4):
        """
        初始化音频下载器
        
        Args:
            downloads_dir: 下载目录
            max_concurrent: 最大并发下载数
            max_threads: 每个下载的最大线程数
        """
        self.downloads_dir = Path(downloads_dir)
        self.max_concurrent = max_concurrent
        self.max_threads = max_threads
        self._download_semaphore = asyncio.Semaphore(max_concurrent)
        self.task_service = AsyncTaskService()
        
        # HTTP客户端配置
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            http2=True,
            follow_redirects=True
        )
    
    def set_max_concurrent(self, n: int):
        """Update maximum concurrent downloads at runtime."""
        n = max(1, int(n))
        self.max_concurrent = n
        self._download_semaphore = asyncio.Semaphore(n)
    
    def set_max_threads(self, n: int):
        """Update default max threads per download at runtime."""
        n = max(1, int(n))
        self.max_threads = n
    


    async def download(self, task_id: int) -> bool:
        """
        下载文件 - 使用任务ID
        
        Args:
            task_id: 任务ID
            
        Returns:
            下载是否成功
        """
        async with self._download_semaphore:
            return await self._download_task(task_id)
    
    async def _download_task(self, task_id: int) -> bool:
        """内部下载实现"""
        try:
            task = await self.task_service.get_task(task_id)
            if not task:
                logger.error(f"Task not found: {task_id}")
                return False
            if not task.file_path:
                logger.error(f"No temporary file path for task: {task_id}")
                return False
            logger.info(f"Starting download for task {task_id}: {task.file_name}")
            
            # 获取下载URL (需要从song controller获取)
            download_url = await self._get_download_url(task_id)
            if not download_url:
                return False
            
            # 执行下载
            success = await self._download_file(task_id, download_url)
            
            return success
            
        except Exception as e:
            logger.exception(f"Download error for task {task_id}: {str(e)}")
            await self.task_service.update_fields(task_id, error_message=str(e))
            return False
    
    async def _get_download_url(self, task_id: int) -> Optional[str]:
        try:
            from ncm.api.ncm.music.song import SongController
            song_controller = SongController()
            
            task = await self.task_service.get_task(task_id)
            if not task:
                return None
            registry = get_task_cache_registry()
            cache = await registry.get_or_create(task.id, task.music_id)
            url_data = await cache.ensure_play_url(song_controller.song_url_v1, level=task.quality or 'lossless', force=False)
            await self.task_service.update_fields(
                task_id,
                quality=url_data["level"],
                file_size=url_data["size"],
                file_format=url_data.get("type", "mp3"),
            )
            return url_data.get("url")
                
        except Exception as e:
            logger.exception(f"Error getting download URL for task {task_id}: {str(e)}")
            return None
    
    async def _download_file(self, task_id: int, url: str) -> bool:
        """下载文件到临时位置"""
        try:
            task = await self.task_service.get_task(task_id)
            if not task:
                return False
            temp_path = Path(task.file_path)
            temp_path.parent.mkdir(parents=True, exist_ok=True)
            # 检查文件大小以决定下载策略
            if task.file_size and task.file_size > 10 * 1024 * 1024:  # 大于10MB使用分段下载
                return await self._download_with_segments(task_id, url)
            else:
                return await self._download_simple(task_id, url)
                
        except Exception as e:
            logger.exception(f"Error downloading file for task {task_id}: {str(e)}")
            return False
    
    async def _download_simple(self, task_id: int, url: str) -> bool:
        try:
            task = await self.task_service.get_task(task_id)
            if not task:
                return False
            temp_path = Path(task.file_path)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with self._client.stream('GET', url, headers=headers) as response:
                if response.status_code == 403:
                    logger.warning(f"Download URL expired for task {task_id}")
                    registry = get_task_cache_registry()
                    cache = registry.get(task_id)
                    if cache:
                        from ncm.api.ncm.music.song import SongController
                        song_controller = SongController()
                        try:
                            new_data = await cache.ensure_play_url(song_controller.song_url_v1, level=task.quality or 'lossless', force=True)
                            url = new_data.get("url")
                        except Exception:
                            await self.task_service.update_fields(task_id, error_message="Download URL expired")
                            return False
                    else:
                        await self.task_service.update_fields(task_id, error_message="Download URL expired")
                        return False
                
                response.raise_for_status()
                
                with open(temp_path, 'wb') as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        f.write(chunk)
                
                logger.info(f"Simple download completed for task {task_id}")
                return True
                
        except Exception as e:
            logger.exception(f"Simple download error for task {task_id}: {str(e)}")
            return False
    
    async def _download_with_segments(self, task_id: int, url: str) -> bool:
        """分段下载 (大文件) - 支持断点续传"""
        try:
            task = await self.task_service.get_task(task_id)
            if not task:
                return False
            
            # 设置缓存目录
            cache_dir = self.downloads_dir / ".cache" / str(task_id)
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            temp_path = Path(task.file_path)
            file_size = task.file_size
            
            # 创建分段
            segment_size = max(4 * 1024 * 1024, file_size // self.max_threads)  # 最小4MB
            segments = []
            
            start = 0
            while start < file_size:
                end = min(start + segment_size - 1, file_size - 1)
                segment_path = cache_dir / f"{task_id}_{start}_{end}.part"
                segments.append({
                    'start': start,
                    'end': end,
                    'file_path': segment_path
                })
                start = end + 1
            
            logger.info(f"Created {len(segments)} segments for task {task_id} in {cache_dir}")
            
            # 并发下载分段
            semaphore = asyncio.Semaphore(self.max_threads)
            
            async def download_segment(index, segment):
                # 断点续传检查：如果分段文件存在且大小正确，跳过下载
                if segment['file_path'].exists():
                    current_size = segment['file_path'].stat().st_size
                    expected_size = segment['end'] - segment['start'] + 1
                    if current_size == expected_size:
                        logger.debug(f"Segment {segment['start']}-{segment['end']} already downloaded, skipping")
                        return True
                    
                async with semaphore:
                    if await self._download_segment(url, segment):
                        logger.info(f"Segment {index} download success for {segment['start']}-{segment['end']}")
                        return True
                    return False
            
            download_tasks = [download_segment(i, seg) for i, seg in enumerate(segments)]
            results = await asyncio.gather(*download_tasks, return_exceptions=True)
            
            # 检查结果
            for i, result in enumerate(results):
                if isinstance(result, Exception) or not result:
                    logger.info(f"Segment {i} download failed for task {task_id}")
                    return False

            # 合并分段
            with open(temp_path, 'wb') as output_file:
                for segment in segments:
                    with open(segment['file_path'], 'rb') as segment_file:
                        shutil.copyfileobj(segment_file, output_file)
            
            # 下载成功后清理缓存
            try:
                for segment in segments:
                    if segment['file_path'].exists():
                        segment['file_path'].unlink()
                if cache_dir.exists():
                    cache_dir.rmdir()
            except Exception as e:
                logger.warning(f"Failed to cleanup cache for task {task_id}: {e}")
            
            logger.info(f"Segmented download completed for task {task_id}")
            return True
            
        except Exception as e:
            logger.exception(f"Segmented download error for task {task_id}: {str(e)}")
            return False
    
    async def _download_segment(self, url: str, segment: dict) -> bool:
        """下载单个分段"""
        try:
            headers = {
                'Range': f'bytes={segment["start"]}-{segment["end"]}',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with self._client.stream('GET', url, headers=headers) as response:
                if response.status_code not in [206, 200]:  # 206 Partial Content or 200 OK
                    return False
                
                with open(segment['file_path'], 'wb') as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        f.write(chunk)

                return True
                
        except Exception as e:
            logger.exception(f"Segment download error: {str(e)}")
            return False
    
    async def close(self):
        """关闭下载器并清理资源"""
        await self._client.aclose()
        logger.info("Audio downloader closed")
