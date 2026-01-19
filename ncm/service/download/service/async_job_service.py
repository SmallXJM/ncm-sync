from __future__ import annotations

from typing import Optional
from ncm.data.async_session import get_uow_factory
from ncm.data.models import DownloadJob
from ncm.data.repositories.async_download_task_repo import AsyncDownloadTaskRepository
from ncm.data.repositories.async_download_job_repo import AsyncDownloadJobRepository
from ncm.core.time import UTC_CLOCK

class AsyncJobService:
    def __init__(self, db_url: Optional[str] = None):
        self.uow_factory = get_uow_factory(db_url)
        self.task_repo = AsyncDownloadTaskRepository()
        self.job_repo = AsyncDownloadJobRepository()

    async def update_job_status(self, job_id: int, status: str):
        async with self.uow_factory() as uow:
            if status == "scanning":
                await self.job_repo.update(uow.session, job_id, status=status, started_at=UTC_CLOCK.now())
            if status in ["downloading", "failed"]:
                await self.job_repo.update(uow.session, job_id, status=status, updated_at=UTC_CLOCK.now())
            else:
                await self.job_repo.update(uow.session, job_id, status=status)

    async def set_job_status_scanning(self, job_id: int):
        await self.update_job_status(job_id, "scanning")

    async def set_job_status_downloading(self, job_id: int):
        await self.update_job_status(job_id, "downloading")

    async def set_job_status_failed(self, job_id: int):
        await self.update_job_status(job_id, "failed")

    # completed
    async def set_job_status_completed(self, job_id: int):
        await self.update_job_status(job_id, "completed")

    async def get_job_all_enabled(self) -> list[DownloadJob]:
        async with self.uow_factory() as uow:
            jobs = await self.job_repo.get_all_enabled(uow.session)
            return jobs
        
