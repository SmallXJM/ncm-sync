"""Workflow execution engine for download orchestrator."""

from ncm.core.logging import get_logger
from ncm.infrastructure.db.models.download_task import TaskProgress
from ncm.service.download.service.async_task_service import AsyncTaskService

logger = get_logger(__name__)


class WorkflowEngine:
    """工作流执行引擎 - 协调各个组件完成下载流程"""
    
    def __init__(self, downloader, metadata_processor, storage_manager):
        """
        初始化工作流引擎
        
        Args:
            downloader: 下载器实例
            metadata_processor: 元数据处理器实例
            storage_manager: 存储管理器实例
        """
        self.downloader = downloader
        self.metadata_processor = metadata_processor
        self.storage_manager = storage_manager
        self.task_service = AsyncTaskService()
    
    async def execute(self, task_id: int):
        """
        执行完整工作流
        
        Args:
            task_id: 下载任务ID（使用唯一键 task.id）
            
        Raises:
            RuntimeError: 当任何步骤失败时抛出异常
        """
        logger.debug(f"Starting workflow execution for task {task_id}")
        
        try:
            # 获取任务和作业配置
            task = await self.task_service.get_task(task_id)
            if not task:
                raise RuntimeError(f"Task not found: {task_id}")
            job = await self.task_service.get_job_for_task(task_id)
            if not job:
                raise RuntimeError(f"Job not found for task {task_id}")
            
            # 1. 音乐下载阶段 (必需)
            await self._execute_music_download(task_id)

            # 2. 元数据任务 (可选)
            if job.embed_metadata:
                await self._execute_metadata_task(task_id)

            # 3. 封面任务 (可选)
            if job.embed_cover:
                await self._execute_cover_task(task_id)

            # 4. 歌词任务 (可选)
            if job.embed_lyrics:
                await self._execute_lyrics_task(task_id)

            # 5. 文件最终化 (必需)
            await self._execute_file_finalization(task_id)
            
            # 6. 检查完成状态
            task = await self.task_service.get_task(task_id)
            job = await self.task_service.get_job_for_task(task_id)
            if not task or not job:
                raise RuntimeError("Task or job not found during completion check")
            
            if TaskProgress.is_fully_completed(task.progress_flags, job):
                await self.task_service.update_status(task_id, "completed")
                logger.debug(f"Workflow completed successfully for task {task_id}")
            else:
                await self.task_service.update_status(task_id, "failed", "Not all required steps completed")
                raise RuntimeError("Not all required steps completed")
            
        except Exception as e:
            logger.error(f"Workflow failed for task {task_id}: {str(e)}")
            await self.task_service.update_status(task_id, "failed", str(e))
            raise
    
    async def _execute_music_download(self, task_id: int):
        """执行音乐下载阶段"""
        logger.debug(f"Starting music download phase for task {task_id}")
        
        # 检查是否已经下载完成
        if await self.task_service.is_flag_set(task_id, TaskProgress.MUSIC_DOWNLOADED):
            logger.debug(f"Music already downloaded for task {task_id}")
            return
        
        # 执行下载
        success = await self.downloader.download(task_id)
        if not success:
            raise RuntimeError(f"Music download failed for task {task_id}")
        
        # 更新进度标志
        await self.task_service.set_progress_music_downloaded(task_id)
        
        logger.debug(f"Music download phase completed for task {task_id}")
    
    async def _execute_metadata_task(self, task_id: int):
        """执行元数据任务 (获取+嵌入+写入一体化)"""
        logger.debug(f"Starting metadata task for task {task_id}")
        
        # 检查是否已经完成
        if await self.task_service.is_flag_set(task_id, TaskProgress.METADATA_COMPLETED):
            logger.debug(f"Metadata task already completed for task {task_id}")
            return
        
        try:
            # 执行元数据任务 (获取+嵌入+写入一体化)
            success = await self.metadata_processor.process_metadata(task_id)
            if success:
                # 更新进度标志
                await self.task_service.set_progress_metadata_completed(task_id)
                logger.debug(f"Metadata task completed for task {task_id}")
            else:
                logger.warning(f"Metadata task failed for task {task_id}, but continuing workflow")
        except Exception as e:
            logger.warning(f"Metadata task error for task {task_id}: {str(e)}, continuing workflow")
    
    async def _execute_cover_task(self, task_id: int):
        """执行封面任务 (获取+嵌入+写入一体化)"""
        logger.debug(f"Starting cover task for task {task_id}")
        
        # 检查是否已经完成
        if await self.task_service.is_flag_set(task_id, TaskProgress.COVER_COMPLETED):
            logger.debug(f"Cover task already completed for task {task_id}")
            return
        
        try:
            # 执行封面任务 (获取+嵌入+写入一体化)
            success = await self.metadata_processor.process_cover(task_id)
            if success:
                # 更新进度标志
                await self.task_service.set_progress_cover_completed(task_id)
                logger.debug(f"Cover task completed for task {task_id}")
            else:
                logger.warning(f"Cover task failed for task {task_id}, but continuing workflow")
        except Exception as e:
            logger.warning(f"Cover task error for task {task_id}: {str(e)}, continuing workflow")
    
    async def _execute_lyrics_task(self, task_id: int):
        """执行歌词任务 (获取+嵌入+写入一体化)"""
        logger.debug(f"Starting lyrics task for task {task_id}")
        
        # 检查是否已经完成
        if await self.task_service.is_flag_set(task_id, TaskProgress.LYRICS_COMPLETED):
            logger.debug(f"Lyrics task already completed for task {task_id}")
            return
        
        try:
            # 执行歌词任务 (获取+嵌入+写入一体化)
            success = await self.metadata_processor.process_lyrics(task_id)
            if success:
                # 更新进度标志
                await self.task_service.set_progress_lyrics_completed(task_id)
                logger.debug(f"Lyrics task completed for task {task_id}")
            else:
                logger.warning(f"Lyrics task failed for task {task_id}, but continuing workflow")
        except Exception as e:
            logger.warning(f"Lyrics task error for task {task_id}: {str(e)}, continuing workflow")
    
    async def _execute_file_finalization(self, task_id: int):
        """执行文件最终化任务"""
        logger.debug(f"Starting file finalization for task {task_id}")
        
        # 检查是否已经完成和音乐文件是否准备就绪
        task = await self.task_service.get_task(task_id)
        if not task:
            raise RuntimeError(f"Task not found: {task_id}")
        
        if TaskProgress.has_flag(task.progress_flags, TaskProgress.FILE_FINALIZED):
            logger.debug(f"File already finalized for task {task_id}")
            return
        
        # 检查音乐文件是否准备就绪
        if not TaskProgress.has_flag(task.progress_flags, TaskProgress.MUSIC_DOWNLOADED):
            raise RuntimeError("Music file not ready for finalization")
        
        # 执行文件最终化
        success = await self.storage_manager.finalize(task_id)
        if not success:
            raise RuntimeError(f"File finalization failed for task {task_id}")
        
        # 更新进度标志
        await self.task_service.set_progress_file_finalized(task_id)
        
        logger.debug(f"File finalization completed for task {task_id}")
