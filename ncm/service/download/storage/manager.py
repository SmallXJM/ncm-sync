"""Storage manager implementation for new task-driven architecture."""

import shutil
from pathlib import Path
from typing import Optional

from ncm.core.logging import get_logger
from ncm.service.download.service.async_task_service import AsyncTaskService
from ncm.infrastructure.db.models.download_job import DownloadJob
from ncm.infrastructure.db.models.download_task import DownloadTask

logger = get_logger(__name__)


class StorageManager:
    """存储管理器 - 处理文件最终化和移动"""

    def __init__(self):
        """初始化存储管理器"""
        self.task_service = AsyncTaskService()

    async def finalize(self, task_id: int) -> bool:
        """
        文件最终化 - 将临时文件移动到最终位置
        
        Args:
            task_id: 任务ID
            
        Returns:
            最终化是否成功
        """
        try:
            logger.debug(f"Starting file finalization for task {task_id}")

            task = await self.task_service.get_task(task_id)
            if not task:
                logger.error(f"Task not found: {task_id}")
                return False
            job = await self.task_service.get_job_for_task(task_id)
            if not job:
                logger.error(f"Job not found: {task_id}")
                return False

            # 验证临时文件存在
            if not task.file_path or not Path(task.file_path).exists():
                error_msg = f"Temporary file not found: {task.file_path}"
                logger.error(error_msg)
                await self.task_service.update_fields(task_id, error_message=error_msg)
                return False

            # 生成最终文件路径
            final_path = self._generate_final_path(task, job)

            # 确保目标目录存在
            final_path.parent.mkdir(parents=True, exist_ok=True)

            # 移动文件到最终位置
            temp_path = Path(task.file_path)
            shutil.move(str(temp_path), str(final_path))

            await self.task_service.update_fields(
                task_id
                , file_path=str(final_path)
                , file_name=final_path.name
            )
            logger.debug(f"File finalized successfully: {final_path}")
            return True

        except Exception as e:
            logger.exception(f"File finalization error for task {task_id}: {str(e)}")
            await self.task_service.update_fields(task_id, error_message=f"Finalization failed: {str(e)}")
            return False

    def _generate_final_path(self, task: DownloadTask, job: DownloadJob) -> Path:
        """
        生成最终文件路径
        
        Args:
            task: 下载任务对象
            job: 下载作业对象
            
        Returns:
            最终文件路径
        """
        # 使用作业的存储路径作为基础
        base_path = Path(job.storage_path)

        # 不直接使用已有文件名
        # 如果任务已有文件名，直接使用
        # if task.file_name:
        #     return base_path / task.file_name

        # 根据模板生成文件名
        template = job.filename_template or "{artist} - {title}"

        # 准备模板变量
        template_vars = {
            'id': task.music_id or 'UnknownID',
            'title': self._sanitize_filename(task.music_title or 'UnknownTitile'),
            'artist': self._sanitize_filename(task.music_artist or 'UnknownArtist'),
            'album': self._sanitize_filename(task.music_album or 'UnknownAlbum'),
            'quality': task.quality or 'UnknownQuality',
            'format': task.file_format or 'UnknownFormat'
        }

        # 生成文件名
        try:
            filename = template.format(**template_vars)
        except KeyError as e:
            logger.warning(f"Template variable not found: {e}, using fallback")
            filename = f"{template_vars['artist']} - {template_vars['title']}"

        # 添加文件扩展名
        if task.file_format and not filename.endswith(f".{task.file_format}"):
            filename = f"{filename}.{task.file_format}"

        return base_path / filename

    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名中的非法字符"""
        if not filename:
            return "Unknown"

        # 替换非法字符
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')

        # 清理首尾空格和点
        filename = filename.strip(' .')

        # 限制长度
        if len(filename) > 100:
            filename = filename[:100]

        return filename or "Unknown"

    # 向后兼容方法 (用于旧的orchestrator调用)
    async def store(self, task_id: int) -> bool:
        """向后兼容的存储方法，实际调用finalize"""
        return await self.finalize(task_id)
