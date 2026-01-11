"""Repository for download job management."""

import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from ncm.infrastructure.db.models.download_job import DownloadJob

logger = logging.getLogger(__name__)


class DownloadJobRepository:
    """Repository for download job configuration management."""
    
    def __init__(self):
        """Initialize repository."""
        pass
    
    def get_by_id(self, session: Session, job_id: int) -> Optional[DownloadJob]:
        """
        Get download job by ID.
        
        Args:
            session: Database session
            job_id: Job ID
            
        Returns:
            DownloadJob model or None if not found
        """
        try:
            return session.query(DownloadJob).filter(
                DownloadJob.id == job_id
            ).first()
        except Exception as e:
            logger.exception(f"Error getting download job: {str(e)}")
            return None

    def get_by_source(self, session: Session, source_type: str, source_id: str) -> Optional[DownloadJob]:
        """
        Get download job by source.
        
        Args:
            session: Database session
            source_type: Source type ('playlist', 'album', 'artist')
            source_id: Source ID
            
        Returns:
            DownloadJob model or None if not found
        """
        try:
            return session.query(DownloadJob).filter(
                DownloadJob.source_type == source_type,
                DownloadJob.source_id == source_id
            ).first()
        except Exception as e:
            logger.exception(f"Error getting download job by source: {str(e)}")
            return None
    
    def get_all_enabled(self, session: Session) -> List[DownloadJob]:
        """
        Get all enabled download jobs.
        
        Args:
            session: Database session
            
        Returns:
            List of enabled DownloadJob models
        """
        try:
            return session.query(DownloadJob).filter(
                DownloadJob.enabled == True
            ).all()
        except Exception as e:
            logger.exception(f"Error getting enabled download jobs: {str(e)}")
            return []
    
    def get_by_status(self, session: Session, status: str) -> List[DownloadJob]:
        """
        Get all jobs with specific status.
        
        Args:
            session: Database session
            status: Job status
            
        Returns:
            List of DownloadJob models
        """
        try:
            return session.query(DownloadJob).filter(
                DownloadJob.status == status
            ).all()
        except Exception as e:
            logger.exception(f"Error getting jobs by status: {str(e)}")
            return []
    
    def get_all(self, session: Session) -> List[DownloadJob]:
        """
        Get all download jobs.
        
        Args:
            session: Database session
            
        Returns:
            List of all DownloadJob models
        """
        try:
            return session.query(DownloadJob).all()
        except Exception as e:
            logger.exception(f"Error getting all download jobs: {str(e)}")
            return []
    
    def create(self, session: Session, job_name: str, job_type: str,
               source_type: str, source_id: str, storage_path: str,
               source_owner_id: str = None, source_name: str = None,
               filename_template: str = '{artist} - {title}',
               target_quality: str = 'lossless',
               embed_cover: bool = True, embed_lyrics: bool = True,
               embed_metadata: bool = True, enabled: bool = True) -> Optional[DownloadJob]:
        """
        Create a new download job.
        
        Args:
            session: Database session
            job_name: Job name
            job_type: Job type ('playlist', 'album', 'artist', 'search', 'manual')
            source_type: Source type ('playlist', 'album', 'artist')
            source_id: Source ID
            storage_path: Storage directory path
            source_owner_id: Source owner ID (optional)
            source_name: Source name (optional)
            filename_template: Filename template
            target_quality: Target quality
            embed_cover: Whether to download cover
            embed_lyrics: Whether to download lyrics
            embed_metadata: Whether to embed metadata
            enabled: Whether to enable this job
            
        Returns:
            Created DownloadJob model or None if failed
        """
        try:
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
            session.flush()
            session.refresh(job)
            logger.info(f"Created download job: {job_name}")
            return job
        except Exception as e:
            logger.exception(f"Error creating download job: {str(e)}")
            return None
    
    def update(self, session: Session, job_id: int, **kwargs) -> Optional[DownloadJob]:
        """
        Update an existing download job.
        
        Args:
            session: Database session
            job_id: Job ID
            **kwargs: Fields to update
            
        Returns:
            Updated DownloadJob model or None if failed
        """
        try:
            job = session.query(DownloadJob).filter(
                DownloadJob.id == job_id
            ).first()
            
            if not job:
                logger.warning(f"Download job not found: {job_id}")
                return None
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            
            session.flush()
            session.refresh(job)
            logger.info(f"Updated download job: {job_id}")
            return job
        except Exception as e:
            logger.exception(f"Error updating download job: {str(e)}")
            return None
    
    def update_statistics(self, session: Session, job_id: int, 
                         total_tasks: int = None, completed_tasks: int = None, 
                         failed_tasks: int = None) -> Optional[DownloadJob]:
        """
        Update job statistics.
        
        Args:
            session: Database session
            job_id: Job ID
            total_tasks: Total tasks count
            completed_tasks: Completed tasks count
            failed_tasks: Failed tasks count
            
        Returns:
            Updated DownloadJob model or None if failed
        """
        try:
            job = session.query(DownloadJob).filter(
                DownloadJob.id == job_id
            ).first()
            
            if not job:
                logger.warning(f"Download job not found: {job_id}")
                return None
            
            if total_tasks is not None:
                job.total_tasks = total_tasks
            if completed_tasks is not None:
                job.completed_tasks = completed_tasks
            if failed_tasks is not None:
                job.failed_tasks = failed_tasks
            
            session.flush()
            session.refresh(job)
            return job
        except Exception as e:
            logger.exception(f"Error updating job statistics: {str(e)}")
            return None
    
    def delete(self, session: Session, job_id: int) -> bool:
        """
        Delete a download job.
        
        Args:
            session: Database session
            job_id: Job ID
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            job = session.query(DownloadJob).filter(
                DownloadJob.id == job_id
            ).first()
            
            if not job:
                logger.warning(f"Download job not found: {job_id}")
                return False
            
            session.delete(job)
            logger.info(f"Deleted download job: {job_id}")
            return True
        except Exception as e:
            logger.exception(f"Error deleting download job: {str(e)}")
            return False
