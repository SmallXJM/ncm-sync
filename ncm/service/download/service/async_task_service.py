from __future__ import annotations

from datetime import datetime
# from turtle import st
from typing import Optional
from ncm.infrastructure.db.async_session import get_uow_factory
from ncm.infrastructure.db.repositories.async_download_task_repo import AsyncDownloadTaskRepository
from ncm.infrastructure.db.repositories.async_download_job_repo import AsyncDownloadJobRepository
from ncm.infrastructure.db.models.download_task import TaskProgress
from ncm.infrastructure.db.models.download_job import DownloadJob
from ncm.infrastructure.db.models.download_task import DownloadTask



class AsyncTaskService:
    def __init__(self, db_url: Optional[str] = None):
        self.uow_factory = get_uow_factory(db_url)
        self.task_repo = AsyncDownloadTaskRepository()
        self.job_repo = AsyncDownloadJobRepository()

    async def get_task(self, task_id: int) -> Optional[DownloadTask]:
        async with self.uow_factory() as uow:
            return await self.task_repo.get_by_id(uow.session, task_id)

    async def get_job_for_task(self, task_id: int) -> Optional[DownloadJob]:
        async with self.uow_factory() as uow:
            task = await self.task_repo.get_by_id(uow.session, task_id)
            if not task:
                return None
            return await self.job_repo.get_by_id(uow.session, task.job_id)

    async def is_flag_set(self, task_id: int, flag: int) -> bool:
        async with self.uow_factory() as uow:
            task = await self.task_repo.get_by_id(uow.session, task_id)
            if not task:
                return False
            return TaskProgress.has_flag(task.progress_flags, flag)

    async def update_job_status(self, job_id: int, status: str):
        async with self.uow_factory() as uow:
            if status == "scanning":
                await self.job_repo.update(uow.session, job_id, status=status, started_at=datetime.utcnow())
            else:
                await self.job_repo.update(uow.session, job_id, status=status)

    async def set_job_status_scanning(self, job_id: int):
        await self.update_job_status(job_id, "scanning")

    async def update_progress(self, task_id: int, progress_flag: int):
        async with self.uow_factory() as uow:
            await self.task_repo.update_progress(uow.session, task_id, progress_flag)

    async def set_progress_music_downloaded(self, task_id: int):
        await self.update_progress(task_id, TaskProgress.MUSIC_DOWNLOADED)

    async def set_progress_metadata_completed(self, task_id: int):
        await self.update_progress(task_id, TaskProgress.METADATA_COMPLETED)

    async def set_progress_cover_completed(self, task_id: int):
        await self.update_progress(task_id, TaskProgress.COVER_COMPLETED)

    async def set_progress_lyrics_completed(self, task_id: int):
        await self.update_progress(task_id, TaskProgress.LYRICS_COMPLETED)

    async def set_progress_file_finalized(self, task_id: int):
        await self.update_progress(task_id, TaskProgress.FILE_FINALIZED)

    

    async def update_status(self, task_id: int, status: str, error_message: Optional[str] = None):
        async with self.uow_factory() as uow:
            await self.task_repo.update_status(uow.session, task_id, status, error_message)

    async def update_fields(self, task_id: int, **kwargs):
        async with self.uow_factory() as uow:
            await self.task_repo.update(uow.session, task_id, **kwargs)

    async def check_fully_completed(self, task_id: int) -> bool:
        async with self.uow_factory() as uow:
            task = await self.task_repo.get_by_id(uow.session, task_id)
            if not task:
                return False
            job = await self.job_repo.get_by_id(uow.session, task.job_id)
            if not job:
                return False
            return TaskProgress.is_fully_completed(task.progress_flags, job)
