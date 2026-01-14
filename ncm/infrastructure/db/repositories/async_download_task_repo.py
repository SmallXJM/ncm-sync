from __future__ import annotations

from typing import Optional, List
from sqlalchemy import select, delete, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from ncm.infrastructure.db.models.download_task import DownloadTask
from ncm.infrastructure.db.models.download_job import DownloadJob

class AsyncDownloadTaskRepository:
    async def get_by_id(self, session: AsyncSession, task_id: int) -> Optional[DownloadTask]:
        result = await session.execute(select(DownloadTask).where(DownloadTask.id == task_id))
        return result.scalar_one_or_none()

    async def get_by_job_and_music(self, session: AsyncSession, job_id: int, music_id: str) -> Optional[DownloadTask]:
        result = await session.execute(
            select(DownloadTask).where(
                DownloadTask.job_id == job_id,
                DownloadTask.music_id == music_id
            )
        )
        return result.scalar_one_or_none()

    async def list_by_job(self, session: AsyncSession, job_id: int) -> List[DownloadTask]:
        result = await session.execute(select(DownloadTask).where(DownloadTask.job_id == job_id))
        return list(result.scalars())

    async def get_by_status(self, session: AsyncSession, status: str) -> List[DownloadTask]:
        result = await session.execute(select(DownloadTask).where(DownloadTask.status == status))
        return list(result.scalars())

    async def get_by_job_and_status(self, session: AsyncSession, job_id: int, status: str) -> List[DownloadTask]:
        result = await session.execute(
            select(DownloadTask).where(
                DownloadTask.job_id == job_id,
                DownloadTask.status == status
            )
        )
        return list(result.scalars())

    async def get_pending_tasks(self, session: AsyncSession, limit: Optional[int] = None) -> List[DownloadTask]:
        stmt = select(DownloadTask).where(DownloadTask.status == "pending").order_by(DownloadTask.created_at)
        if limit:
            stmt = stmt.limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars())

    async def create(self, session: AsyncSession, music_id: str, job_id: int,
                     music_title: Optional[str] = None, music_artist: Optional[str] = None,
                     music_album: Optional[str] = None) -> Optional[DownloadTask]:
        task = DownloadTask(
            music_id=music_id,
            job_id=job_id,
            music_title=music_title,
            music_artist=music_artist,
            music_album=music_album,
            status="pending"
        )
        session.add(task)
        await session.flush()
        await session.refresh(task)
        return task

    async def create_batch(self, session: AsyncSession, tasks_data: List[dict]) -> List[DownloadTask]:
        tasks: List[DownloadTask] = []
        for data in tasks_data:
            task = DownloadTask(
                music_id=data.get("music_id"),
                job_id=data.get("job_id"),
                music_title=data.get("music_title"),
                music_artist=data.get("music_artist"),
                music_album=data.get("music_album"),
                status=data.get("status", "pending")
            )
            tasks.append(task)
        session.add_all(tasks)
        await session.flush()
        for task in tasks:
            await session.refresh(task)
        return tasks

    async def update(self, session: AsyncSession, task_id: int, **kwargs) -> Optional[DownloadTask]:
        task = await self.get_by_id(session, task_id)
        if not task:
            return None
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        await session.flush()
        await session.refresh(task)
        return task

    async def update_progress(self, session: AsyncSession, task_id: int, progress_flag: int) -> Optional[DownloadTask]:
        task = await self.get_by_id(session, task_id)
        if not task:
            return None
        task.progress_flags = task.progress_flags | progress_flag
        await session.flush()
        await session.refresh(task)
        return task

    async def update_status(self, session: AsyncSession, task_id: int, status: str,
                            error_message: Optional[str] = None) -> Optional[DownloadTask]:
        task = await self.get_by_id(session, task_id)
        if not task:
            return None
        task.status = status
        if error_message is not None:
            task.error_message = error_message
        await session.flush()
        await session.refresh(task)
        return task

    # async def increment_retry_count(self, session: AsyncSession, task_id: int) -> Optional[DownloadTask]:
    #     task = await self.get_by_id(session, task_id)
    #     if not task:
    #         return None
    #     task.retry_count = (task.retry_count or 0) + 1
    #     await session.flush()
    #     await session.refresh(task)
    #     return task

    async def delete(self, session: AsyncSession, task_id: int) -> bool:
        task = await self.get_by_id(session, task_id)
        if not task:
            return False
        await session.delete(task)
        return True

    async def delete_by_job(self, session: AsyncSession, job_id: int) -> int:
        result = await session.execute(delete(DownloadTask).where(DownloadTask.job_id == job_id))
        return result.rowcount or 0

    async def find_completed_by_music_and_quality(self, session: AsyncSession, music_id: str, target_quality: str) -> Optional[DownloadTask]:
        stmt = (
            select(DownloadTask)
            .join(DownloadJob, DownloadTask.job_id == DownloadJob.id)
            .where(
                DownloadTask.music_id == music_id,
                DownloadTask.status == "completed",
                DownloadJob.target_quality == target_quality,
            )
            .order_by(DownloadTask.updated_at.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def search(
        self,
        session: AsyncSession,
        job_id: Optional[int] = None,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[List[DownloadTask], int]:
        stmt = select(DownloadTask)
        
        if job_id is not None:
            stmt = stmt.where(DownloadTask.job_id == job_id)
        if status:
            stmt = stmt.where(DownloadTask.status == status)
        if keyword:
            keyword = f"%{keyword}%"
            stmt = stmt.where(
                or_(
                    DownloadTask.music_title.ilike(keyword),
                    DownloadTask.music_artist.ilike(keyword),
                    DownloadTask.music_album.ilike(keyword),
                    DownloadTask.music_id.ilike(keyword)
                )
            )
            
        # Count query
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await session.execute(count_stmt)).scalar_one()
        
        # Result query
        stmt = stmt.order_by(DownloadTask.created_at.desc()).limit(limit).offset(offset)
        result = await session.execute(stmt)
        return list(result.scalars()), total

