"""Task management for download orchestrator."""

import asyncio
from typing import Dict, Set

from ncm.core.logging import get_logger

logger = get_logger(__name__)


class TaskManager:
    """任务管理器 - 管理下载任务的生命周期 (内存中的异步任务管理)"""
    
    def __init__(self):
        # 只管理内存中的异步任务Future，数据库状态由Repository管理
        self._task_futures: Dict[int, asyncio.Task] = {}
        self._active_task_ids: Set[int] = set()
    
    def register_task(self, task_id: int, future: asyncio.Task):
        """注册异步任务"""
        self._task_futures[task_id] = future
        self._active_task_ids.add(task_id)
        logger.debug(f"Registered async task {task_id}")
    
    def cancel_task(self, task_id: int) -> bool:
        """取消异步任务"""
        future = self._task_futures.get(task_id)
        if future and not future.done():
            future.cancel()
            logger.debug(f"Cancelled async task {task_id}")
            return True
        return False
    
    def mark_completed(self, task_id: int):
        """标记任务完成 (清理内存中的Future)"""
        self._active_task_ids.discard(task_id)
        self._task_futures.pop(task_id, None)
        logger.debug(f"Marked async task {task_id} as completed")
    
    def get_active_task_ids(self) -> Set[int]:
        """获取活跃的任务ID列表"""
        return self._active_task_ids.copy()
    
    def cleanup_completed_futures(self):
        """清理已完成的Future对象"""
        completed_tasks = []
        for task_id, future in self._task_futures.items():
            if future.done():
                completed_tasks.append(task_id)
        
        for task_id in completed_tasks:
            self._active_task_ids.discard(task_id)
            del self._task_futures[task_id]
        
        if completed_tasks:
            logger.debug(f"Cleaned up {len(completed_tasks)} completed futures")
    
    def get_stats(self) -> Dict[str, int]:
        """获取内存任务统计信息"""
        return {
            "active_futures": len(self._task_futures),
            "active_task_ids": len(self._active_task_ids)
        }
