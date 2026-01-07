from __future__ import annotations

from typing import Optional
from ncm.infrastructure.db.async_session import get_uow_factory
from ncm.infrastructure.db.repositories.async_download_task_repo import AsyncDownloadTaskRepository
from ncm.infrastructure.db.repositories.async_download_job_repo import AsyncDownloadJobRepository

class DownloadAsyncService:
    def __init__(self, db_url: Optional[str] = None):
        self.uow_factory = get_uow_factory(db_url)
        self.task_repo = AsyncDownloadTaskRepository()
        self.job_repo = AsyncDownloadJobRepository()

    async def mark_downloading(self, task_id: int) -> None:
        async with self.uow_factory() as uow:
            await self.task_repo.update_status(uow.session, task_id, "downloading")

    async def mark_completed(self, task_id: int) -> None:
        async with self.uow_factory() as uow:
            await self.task_repo.update_status(uow.session, task_id, "completed")

    async def get_task_with_job(self, task_id: int) -> Optional[dict]:
        async with self.uow_factory() as uow:
            task = await self.task_repo.get_by_id(uow.session, task_id)
            if not task:
                return None
            job = await self.job_repo.get_by_id(uow.session, task.job_id)
            return {
                "task": task.to_dict(),
                "job": job.to_dict() if job else None,
            }
