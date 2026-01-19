"""Core download orchestrator implementation."""

import asyncio
import uuid
from pathlib import Path
from typing import Optional, Dict, Any

from ncm.infrastructure.db.models.download_task import DownloadTask, TaskProgress
from ncm.infrastructure.db.models.download_job import DownloadJob
from ncm.infrastructure.db.repositories.async_download_task_repo import AsyncDownloadTaskRepository
from ncm.infrastructure.db.repositories.async_download_job_repo import AsyncDownloadJobRepository
from ncm.infrastructure.utils.path import sanitize_filename
from ncm.service.download.service import AsyncJobService
from ncm.infrastructure.db.async_session import get_uow_factory
from ncm.service.download.models import get_task_cache_registry
from ncm.infrastructure.utils.time import UTC_CLOCK
from ..downloader import AudioDownloader
from ..metadata import MetadataProcessor
from ..storage import StorageManager
from .workflow import WorkflowEngine
from .task_manager import TaskManager
from ncm.core.logging import get_logger



logger = get_logger(__name__)


class DownloadOrchestrator:
    """下载编排器 - 协调整个下载流程"""

    def __init__(self,
                 downloads_dir: str = "downloads",
                 max_concurrent_downloads: int = 3,
                 max_threads_per_download: int = 4):
        """
        初始化下载编排器
        
        Args:
            downloads_dir: 临时下载目录
            max_concurrent_downloads: 最大并发下载数
            max_threads_per_download: 每个下载的最大线程数
        """
        self.downloads_dir = Path(downloads_dir)
        self.downloads_dir.mkdir(parents=True, exist_ok=True)

        # 初始化各个组件
        self.downloader = AudioDownloader(
            downloads_dir=downloads_dir,
            max_concurrent=max_concurrent_downloads,
            max_threads=max_threads_per_download
        )
        self.metadata_processor = MetadataProcessor()
        self.storage_manager = StorageManager()

        # 工作流和任务管理
        self.workflow_engine = WorkflowEngine(
            downloader=self.downloader,
            metadata_processor=self.metadata_processor,
            storage_manager=self.storage_manager
        )
        self.task_manager = TaskManager()

        # 异步数据库单元与仓库（统一管理的 DB URL）
        self.uow_factory = get_uow_factory()
        self.task_repo = AsyncDownloadTaskRepository()
        self.job_repo = AsyncDownloadJobRepository()

        self.job_service = AsyncJobService()

        # 懒加载控制器
        self._song_controller = None
        self._playlist_controller = None
        self._copy_locks: dict[str, asyncio.Lock] = {}
    
    @property
    def song_controller(self):
        """懒加载歌曲控制器"""
        if self._song_controller is None:
            from ncm.api.ncm.music.song import SongController
            self._song_controller = SongController()
        return self._song_controller
    
    @property
    def playlist_controller(self):
        """懒加载歌单控制器"""
        if self._playlist_controller is None:
            from ncm.api.ncm.music.playlist import PlaylistController
            self._playlist_controller = PlaylistController()
        return self._playlist_controller

    async def submit_download(self,
                             music_id: str,
                             job_id: int,
                             target_quality: str = 'lossless') -> int:
        """
        提交下载任务 (非阻塞)
        
        Args:
            music_id: 音乐ID
            job_id: 下载作业ID
            target_quality: 目标音质
            
        Returns:
            任务ID
        """
        async with self.uow_factory() as uow:
            existing_task = await self.task_repo.get_by_job_and_music(uow.session, job_id, music_id)
            if existing_task:
                logger.info(f"Task already exists for music {music_id} in job {job_id}")
                return existing_task.id
            task = await self.task_repo.create(uow.session, music_id=music_id, job_id=job_id)
            if not task:
                raise RuntimeError(f"Failed to create task for music {music_id}")
        registry = get_task_cache_registry()
        await registry.prefetch(task.id, music_id)
        future = asyncio.create_task(self._execute_download_workflow(task.id, target_quality))
        self.task_manager.register_task(task.id, future)
        logger.info(f"Submitted download task {task.id} for music_id: {music_id}")
        return task.id

    async def get_task(self, task_id: int) -> Optional[DownloadTask]:
        """获取任务状态"""
        async with self.uow_factory() as uow:
            return await self.task_repo.get_by_id(uow.session, task_id)

    async def get_task_dict(self, task_id: int) -> Optional[dict]:
        """获取任务字典数据 (避免detached instance问题)"""
        async with self.uow_factory() as uow:
            task = await self.task_repo.get_by_id(uow.session, task_id)
            return task.to_dict() if task else None

    async def cancel_task(self, task_id: int) -> bool:
        """取消任务"""
        # 取消内存中的任务
        memory_cancelled = self.task_manager.cancel_task(task_id)

        async with self.uow_factory() as uow:
            task = await self.task_repo.update_status(uow.session, task_id, "cancelled")
            if task:
                logger.info(f"Cancelled task {task_id}")
                return True

        return memory_cancelled

    async def reset_task(self, task_id: int) -> bool:
        """重置任务状态为 pending"""
        async with self.uow_factory() as uow:
            task = await self.task_repo.update_status(uow.session, task_id, "pending", error_message="")
            if task:
                # Clear progress flags related to completion
                task.progress_flags = 0
                await uow.session.flush()
                logger.info(f"Reset task {task_id} to pending")
                return True
        return False

    async def list_active_tasks(self) -> Dict[int, DownloadTask]:
        """列出活跃任务"""
        async with self.uow_factory() as uow:
            tasks_downloading = await self.task_repo.get_by_status(uow.session, "downloading")
            tasks_processing = await self.task_repo.get_by_status(uow.session, "processing")
            active_tasks = tasks_downloading + tasks_processing
            return {task.id: task for task in active_tasks}

    async def list_active_tasks_dict(self) -> Dict[int, dict]:
        """列出活跃任务字典数据 (避免detached instance问题)"""
        async with self.uow_factory() as uow:
            tasks_downloading = await self.task_repo.get_by_status(uow.session, "downloading")
            tasks_processing = await self.task_repo.get_by_status(uow.session, "processing")
            active_tasks = tasks_downloading + tasks_processing
            return {task.id: task.to_dict() for task in active_tasks}

    async def list_all_tasks(self) -> Dict[int, DownloadTask]:
        """列出所有任务"""
        async with self.uow_factory() as uow:
            # SQLAlchemy 2.0 async 不支持同步的 session.query
            tasks = await self.task_repo.get_by_status(uow.session, "pending")
            tasks += await self.task_repo.get_by_status(uow.session, "downloading")
            tasks += await self.task_repo.get_by_status(uow.session, "processing")
            tasks += await self.task_repo.get_by_status(uow.session, "completed")
            tasks += await self.task_repo.get_by_status(uow.session, "failed")
            return {task.id: task for task in tasks}

    async def search_tasks(self,
                          job_id: Optional[int] = None,
                          status: Optional[str] = None,
                          keyword: Optional[str] = None,
                          limit: int = 20,
                          offset: int = 0) -> Dict[str, Any]:
        """搜索任务 (支持分页)"""
        async with self.uow_factory() as uow:
            tasks, total = await self.task_repo.search(
                uow.session,
                job_id=job_id,
                status=status,
                keyword=keyword,
                limit=limit,
                offset=offset
            )
            return {
                "tasks": [task.to_dict() for task in tasks],
                "total": total,
                "limit": limit,
                "offset": offset
            }

    async def create_download_job(self,
                                 job_name: str,
                                 job_type: str,
                                 source_type: str,
                                 source_id: str,
                                 storage_path: str,
                                 source_owner_id: str = None,
                                 source_name: str = None,
                                 filename_template: str = '{artist} - {title}',
                                 target_quality: str = 'lossless',
                                 embed_cover: bool = True,
                                 embed_lyrics: bool = True,
                                 embed_metadata: bool = True) -> int:
        """
        创建下载作业
        
        Args:
            job_name: 作业名称
            job_type: 作业类型 ('playlist', 'album', 'artist', 'search', 'manual')
            source_type: 源类型 ('playlist', 'album', 'artist')
            source_id: 源ID
            storage_path: 存储路径
            source_owner_id: 源所有者ID (可选)
            source_name: 源名称 (可选)
            filename_template: 文件名模板
            target_quality: 目标音质
            embed_cover: 是否下载封面
            embed_lyrics: 是否下载歌词
            embed_metadata: 是否嵌入元数据
            
        Returns:
            作业ID
        """
        async with self.uow_factory() as uow:
            job = await self.job_repo.create(
                uow.session,
                job_name=job_name,
                job_type=job_type,
                source_type=source_type,
                source_id=source_id,
                storage_path=storage_path,
                source_owner_id=source_owner_id,
                source_name=source_name,
                filename_template=filename_template,
                target_quality=target_quality,
                embed_cover=embed_cover,
                embed_lyrics=embed_lyrics,
                embed_metadata=embed_metadata
            )
            if not job:
                raise RuntimeError(f"Failed to create download job: {job_name}")
            logger.info(f"Created download job: {job_name} (ID: {job.id})")
            return job.id

    async def get_download_job(self, job_id: int) -> Optional[DownloadJob]:
        """获取下载作业"""
        async with self.uow_factory() as uow:
            return await self.job_repo.get_by_id(uow.session, job_id)

    async def get_download_job_dict(self, job_id: int) -> Optional[dict]:
        """获取下载作业字典数据 (避免detached instance问题)"""
        async with self.uow_factory() as uow:
            job = await self.job_repo.get_by_id(uow.session, job_id)
            return job.to_dict() if job else None

    async def update_download_job(self, job_id: int, **fields) -> Optional[DownloadJob]:
        async with self.uow_factory() as uow:
            job = await self.job_repo.update(uow.session, job_id, **fields)
            return job

    async def update_download_job_dict(self, job_id: int, **fields) -> Optional[dict]:
        async with self.uow_factory() as uow:
            job = await self.job_repo.update(uow.session, job_id, **fields)
            return job.to_dict() if job else None

    async def delete_download_job(self, job_id: int) -> bool:
        async with self.uow_factory() as uow:
            result = await self.job_repo.delete(uow.session, job_id)
            return result

    async def list_download_jobs(self) -> list[DownloadJob]:
        """列出所有下载作业"""
        async with self.uow_factory() as uow:
            return await self.job_repo.get_all(uow.session)

    async def list_download_jobs_dict(self) -> list[dict]:
        """列出所有下载作业字典数据 (避免detached instance问题)"""
        async with self.uow_factory() as uow:
            jobs = await self.job_repo.get_all(uow.session)
            return [job.to_dict() for job in jobs]

    async def submit_batch_download(self, job_id: int, music_ids: list[str]) -> list[int]:
        """
        批量提交下载任务
        
        Args:
            job_id: 作业ID
            music_ids: 音乐ID列表
            
        Returns:
            任务ID列表
        """
        task_ids: list[int] = []

        async with self.uow_factory() as uow:
            job = await self.job_repo.get_by_id(uow.session, job_id)
            if not job:
                raise RuntimeError(f"Job not found: {job_id}")

        for music_id in music_ids:
            try:
                task_id = await self.submit_download(music_id, job_id, job.target_quality)
                task_ids.append(task_id)
            except Exception as e:
                logger.warning(f"Failed to submit task for music {music_id}: {e}")
                continue

        async with self.uow_factory() as uow:
            await self.job_repo.update_statistics(uow.session, job_id, total_tasks=len(task_ids))

        logger.info(f"Submitted {len(task_ids)} tasks for job {job_id}")
        return task_ids


    async def upgrade_task_quality(self, job_id: int, music_id: str, new_target_quality: str) -> int:
        """
        升级任务音质 (重启任务)
        
        Args:
            job_id: 作业ID
            music_id: 音乐ID
            new_target_quality: 新的目标音质
            
        Returns:
            新任务ID
        """
        async with self.uow_factory() as uow:
            existing_task = await self.task_repo.get_by_job_and_music(uow.session, job_id, music_id)
            if existing_task:
                await self.cancel_task(existing_task.id)
                await self.task_repo.delete(uow.session, existing_task.id)
                logger.info(f"Removed existing task {existing_task.id} for quality upgrade")
            # job = await self.job_repo.get_by_id(uow.session, job_id)
            # if job and job.target_quality != new_target_quality:
                # await self.job_repo.update(uow.session, job_id, target_quality=new_target_quality)
                # logger.info(f"Updated job {job_id} target quality to {new_target_quality}")

        # 创建新任务
        new_task_id = await self.submit_download(music_id, job_id, new_target_quality)
        logger.info(f"Created new task {new_task_id} for quality upgrade to {new_target_quality}")

        registry = get_task_cache_registry()
        await registry.prefetch(new_task_id, music_id)
        return new_task_id

    async def restart_failed_tasks(self, job_id: int) -> list[int]:
        """
        重启失败的任务
        
        Args:
            job_id: 作业ID
            
        Returns:
            重启的任务ID列表
        """
        restarted_tasks: list[int] = []

        async with self.uow_factory() as uow:
            job = await self.job_repo.get_by_id(uow.session, job_id)
            if not job:
                logger.warning(f"Job not found: {job_id}")
                return restarted_tasks
            failed_tasks = await self.task_repo.get_by_job_and_status(uow.session, job_id, "failed")

            for task in failed_tasks:
                try:
                    # 重置任务状态
                    async with self.uow_factory() as inner_uow:
                        # 更新任务状态为pending
                        await self.task_repo.update(inner_uow.session, task.id,
                        status="pending",
                        progress_flags=0,
                        error_message=None,
                        started_at=None,
                        completed_at=None
                    )

                    # 重新提交任务
                    registry = get_task_cache_registry()
                    await registry.prefetch(task.id, task.music_id)
                    asyncio.create_task(self._execute_download_workflow(task.id, job.target_quality))
                    restarted_tasks.append(task.id)

                except Exception as e:
                    logger.warning(f"Failed to restart task {task.id}: {e}")


        logger.info(f"Restarted {len(restarted_tasks)} failed tasks for job {job_id}")
        return restarted_tasks

    def cleanup_completed_tasks(self):
        """清理完成的内存任务"""
        self.task_manager.cleanup_completed_futures()

    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        memory_stats = self.task_manager.get_stats()

        async with self.uow_factory() as uow:
            downloading = await self.task_repo.get_by_status(uow.session, "downloading")
            processing = await self.task_repo.get_by_status(uow.session, "processing")
            completed = await self.task_repo.get_by_status(uow.session, "completed")
            failed = await self.task_repo.get_by_status(uow.session, "failed")
            total_tasks = len(downloading) + len(processing) + len(completed) + len(failed)
            active_tasks = len(downloading) + len(processing)
            completed_tasks = len(completed)
            failed_tasks = len(failed)

        return {
            'memory': memory_stats,
            'database': {
                'total_tasks': total_tasks,
                'active_tasks': active_tasks,
                'completed_tasks': completed_tasks,
                'failed_tasks': failed_tasks
            }
        }
    
    def get_current_speed(self) -> int:
        """
        获取当前整体下载速度（字节/秒）。
        
        Returns:
            当前下载速度，单位为 byte/s。
        """
        try:
            if not self.downloader:
                return 0
            return int(max(0, self.downloader.get_current_speed()))
        except Exception as e:
            logger.warning(f"Error getting current download speed: {e}")
            return 0

    async def wait_for_task(self, task_id: int) -> Optional[DownloadTask]:
        """
        等待任务完成
        
        Args:
            task_id: 任务ID
            
        Returns:
            完成的任务对象，如果任务不存在则返回None
        """
        while True:
            async with self.uow_factory() as uow:
                task = await self.task_repo.get_by_id(uow.session, task_id)
                if not task:
                    return None
                if task.status in ["completed", "failed", "cancelled"]:
                    return task
            await asyncio.sleep(0.1)


    async def _execute_download_workflow(self, task_id: int, target_quality: str):
        """执行下载工作流"""
        try:
            logger.debug(f"Starting download workflow for task {task_id}")

            # 更新任务状态为下载中
            async with self.uow_factory() as uow:
                await self.task_repo.update_status(uow.session, task_id, "downloading")

            # 1. 准备下载信息
            await self._prepare_download_info(task_id, target_quality)

            # 2. 执行工作流
            await self.workflow_engine.execute(task_id)

        except Exception as e:
            logger.exception(f"Download workflow failed for task {task_id}: {str(e)}")
            async with self.uow_factory() as uow:
                await self.task_repo.update_status(uow.session, task_id, "failed", str(e))
        finally:
            # 更新完成时间
            async with self.uow_factory() as uow:
                task = await self.task_repo.get_by_id(uow.session, task_id)
                if task:
                    await self.task_repo.update(uow.session, task_id, completed_at=UTC_CLOCK.now())

            get_task_cache_registry().clear(task_id)
            self.task_manager.mark_completed(task_id)

    async def _prepare_download_info(self, task_id: int, target_quality: str):
        logger.debug(f"Preparing download info for task {task_id}")

        async with self.uow_factory() as uow:
            task = await self.task_repo.get_by_id(uow.session, task_id)
            if not task:
                raise RuntimeError(f"Task not found: {task_id}")
            registry = get_task_cache_registry()
            cache = await registry.get_or_create(task_id, task.music_id)
            song_info = await cache.ensure_song_detail(
                self.song_controller.song_detail,
                force=(cache.song_detail is None)
            )

            title = song_info["name"]
            artists = [artist["name"] for artist in song_info.get("ar", [])]
            artist = ", ".join(artists) if artists else "Unknown Artist"

            await self.task_repo.update(uow.session, task_id,
                music_title=title,
                music_artist=artist,
                music_album=song_info.get("al", {}).get("name", "Unknown Album"),
                started_at=UTC_CLOCK.now()
            )

        async with self.uow_factory() as uow:
            url_data = await cache.ensure_play_url(
                self.song_controller.song_url_v1,
                level=target_quality,
                force=(cache.play_url is None)
            )
            safe_title = sanitize_filename(title)
            safe_artist = sanitize_filename(artist)
            file_format = url_data.get("type", "mp3")
            filename = f"{safe_artist} - {safe_title}.{file_format}"
            temp_file_path = str(self.downloads_dir / filename)
            await self.task_repo.update(uow.session, task_id,
                quality=url_data["level"],
                file_path=temp_file_path,
                file_name=filename,
                file_format=file_format.lower(),
                file_size=url_data["size"],
            )
        logger.debug(f"Download info prepared for task {task_id}: {title} by {artist}, actual quality: {url_data['level']}")


    # 向后兼容方法
    async def download(self,
                       music_id: str,
                       job_id: int,
                       target_quality: str = 'lossless',
                       progress_callback: Optional[callable] = None) -> DownloadTask:
        """
        下载音乐文件 (向后兼容方法)
        
        Args:
            music_id: 音乐ID
            job_id: 下载作业ID
            target_quality: 目标音质
            progress_callback: 进度回调函数
            
        Returns:
            下载任务对象
        """
        # 提交任务
        task_id = await self.submit_download(music_id, job_id, target_quality)

        # 如果有进度回调，启动监控
        if progress_callback:
            asyncio.create_task(self._monitor_progress(task_id, progress_callback))

        # 等待完成
        result = await self.wait_for_task(task_id)
        return result or DownloadTask(
            task_id=task_id,
            music_id=music_id,
            job_id=job_id,
            status="failed",
            error_message="Task not found or failed to execute"
        )

    async def _monitor_progress(self, task_id: int, progress_callback: callable):
        """监控任务进度"""
        while True:
            async with self.uow_factory() as uow:
                task = await self.task_repo.get_by_id(uow.session, task_id)
                if not task:
                    break
                try:
                    progress_callback(task)
                except Exception as e:
                    logger.warning(f"Progress callback error: {e}")
                if task.status in ["completed", "failed", "cancelled"]:
                    break
            await asyncio.sleep(0.5)

    async def close(self):
        """关闭编排器并清理资源"""
        await self.downloader.close()
        logger.info("Download orchestrator closed")

    def update_concurrency_settings(self, max_concurrent: int, max_threads: int):
        """线程安全的更新并发设置"""
        # 这里可以是简单的赋值，也可以包含更复杂的锁逻辑
        if self.downloader:
            if self.downloader.max_concurrent != max_concurrent:
                logger.info(f"Updating max_concurrent: {self.downloader.max_concurrent} -> {max_concurrent}")
                self.downloader.set_max_concurrent(max_concurrent)

            if self.downloader.max_threads != max_threads:
                logger.info(f"Updating max_threads: {self.downloader.max_threads} -> {max_threads}")
                self.downloader.set_max_threads(max_threads)
