from __future__ import annotations

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ncm.infrastructure.db.models.download_job import DownloadJob

class AsyncDownloadJobRepository:
    async def get_by_id(self, session: AsyncSession, job_id: int) -> Optional[DownloadJob]:
        result = await session.execute(select(DownloadJob).where(DownloadJob.id == job_id))
        return result.scalar_one_or_none()

    async def get_by_source(self, session: AsyncSession, source_type: str, source_id: str) -> Optional[DownloadJob]:
        result = await session.execute(
            select(DownloadJob).where(
                DownloadJob.source_type == source_type,
                DownloadJob.source_id == source_id
            )
        )
        return result.scalar_one_or_none()

    async def get_all_enabled(self, session: AsyncSession) -> List[DownloadJob]:
        result = await session.execute(select(DownloadJob).where(DownloadJob.enabled == True))
        return list(result.scalars())

    async def get_by_status(self, session: AsyncSession, status: str) -> List[DownloadJob]:
        result = await session.execute(select(DownloadJob).where(DownloadJob.status == status))
        return list(result.scalars())

    async def get_all(self, session: AsyncSession) -> List[DownloadJob]:
        result = await session.execute(select(DownloadJob))
        return list(result.scalars())

    async def create(self, session: AsyncSession, job_name: str, job_type: str,
                     source_type: str, source_id: str, storage_path: str,
                     source_owner_id: Optional[str] = None, source_name: Optional[str] = None,
                     filename_template: str = "{artist} - {title}",
                     target_quality: str = "lossless",
                     embed_cover: bool = True, embed_lyrics: bool = True,
                     embed_metadata: bool = True, enabled: bool = True) -> Optional[DownloadJob]:
        job = DownloadJob(
            job_name=job_name,
            job_type=job_type,
            source_type=source_type,
            source_id=source_id,
            source_owner_id=source_owner_id,
            source_name=source_name,
            storage_path=storage_path,
            filename_template=filename_template,
            target_quality=target_quality,
            embed_cover=embed_cover,
            embed_lyrics=embed_lyrics,
            embed_metadata=embed_metadata,
            enabled=enabled
        )
        session.add(job)
        await session.flush()
        await session.refresh(job)
        return job

    async def update(self, session: AsyncSession, job_id: int, **kwargs) -> Optional[DownloadJob]:
        job = await self.get_by_id(session, job_id)
        if not job:
            return None
        for key, value in kwargs.items():
            if hasattr(job, key):
                setattr(job, key, value)
        await session.flush()
        await session.refresh(job)
        return job

    async def update_statistics(self, session: AsyncSession, job_id: int,
                                total_tasks: Optional[int] = None, completed_tasks: Optional[int] = None,
                                failed_tasks: Optional[int] = None) -> Optional[DownloadJob]:
        job = await self.get_by_id(session, job_id)
        if not job:
            return None
        if total_tasks is not None:
            job.total_tasks = total_tasks
        if completed_tasks is not None:
            job.completed_tasks = completed_tasks
        if failed_tasks is not None:
            job.failed_tasks = failed_tasks
        await session.flush()
        await session.refresh(job)
        return job

    async def delete(self, session: AsyncSession, job_id: int) -> bool:
        job = await self.get_by_id(session, job_id)
        if not job:
            return False
        await session.delete(job)
        return True
