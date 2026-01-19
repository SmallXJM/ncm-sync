"""Repository for download task management."""

import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from ncm.data.models.download_task import DownloadTask

logger = logging.getLogger(__name__)


class DownloadTaskRepository:
    """Repository for download task management."""
    
    def __init__(self):
        """Initialize repository."""
        pass
    
    def get_by_id(self, session: Session, task_id: int) -> Optional[DownloadTask]:
        """
        Get download task by ID.
        
        Args:
            session: Database session
            task_id: Task ID
            
        Returns:
            DownloadTask model or None if not found
        """
        try:
            return session.query(DownloadTask).filter(
                DownloadTask.id == task_id
            ).first()
        except Exception as e:
            logger.exception(f"Error getting download task: {str(e)}")
            return None
    
    def get_by_job_and_music(self, session: Session, job_id: int, music_id: str) -> Optional[DownloadTask]:
        """
        Get download task by job and music.
        
        Args:
            session: Database session
            job_id: Job ID
            music_id: Music ID
            
        Returns:
            DownloadTask model or None if not found
        """
        try:
            return session.query(DownloadTask).filter(
                DownloadTask.job_id == job_id,
                DownloadTask.music_id == music_id
            ).first()
        except Exception as e:
            logger.exception(f"Error getting task by job and music: {str(e)}")
            return None
    
    def get_by_job(self, session: Session, job_id: int) -> List[DownloadTask]:
        """
        Get all tasks for a job.
        
        Args:
            session: Database session
            job_id: Job ID
            
        Returns:
            List of DownloadTask models
        """
        try:
            return session.query(DownloadTask).filter(
                DownloadTask.job_id == job_id
            ).all()
        except Exception as e:
            logger.exception(f"Error getting tasks by job: {str(e)}")
            return []
    
    def get_by_status(self, session: Session, status: str) -> List[DownloadTask]:
        """
        Get all tasks with specific status.
        
        Args:
            session: Database session
            status: Task status
            
        Returns:
            List of DownloadTask models
        """
        try:
            return session.query(DownloadTask).filter(
                DownloadTask.status == status
            ).all()
        except Exception as e:
            logger.exception(f"Error getting tasks by status: {str(e)}")
            return []
    
    def get_by_job_and_status(self, session: Session, job_id: int, status: str) -> List[DownloadTask]:
        """
        Get tasks by job and status.
        
        Args:
            session: Database session
            job_id: Job ID
            status: Task status
            
        Returns:
            List of DownloadTask models
        """
        try:
            return session.query(DownloadTask).filter(
                DownloadTask.job_id == job_id,
                DownloadTask.status == status
            ).all()
        except Exception as e:
            logger.exception(f"Error getting tasks by job and status: {str(e)}")
            return []
    
    def get_pending_tasks(self, session: Session, limit: int = None) -> List[DownloadTask]:
        """
        Get pending tasks for processing.
        
        Args:
            session: Database session
            limit: Maximum number of tasks to return
            
        Returns:
            List of pending DownloadTask models
        """
        try:
            query = session.query(DownloadTask).filter(
                DownloadTask.status == 'pending'
            ).order_by(DownloadTask.created_at)
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
        except Exception as e:
            logger.exception(f"Error getting pending tasks: {str(e)}")
            return []
    
    def create(self, session: Session, music_id: str, job_id: int,
               music_title: str = None, music_artist: str = None, 
               music_album: str = None) -> Optional[DownloadTask]:
        """
        Create a new download task.
        
        Args:
            session: Database session
            music_id: Music ID
            job_id: Job ID
            music_title: Music title (optional)
            music_artist: Music artist (optional)
            music_album: Music album (optional)
            
        Returns:
            Created DownloadTask model or None if failed
        """
        try:
            task = DownloadTask(
                music_id=music_id,
                job_id=job_id,
                music_title=music_title,
                music_artist=music_artist,
                music_album=music_album,
                status='pending'
            )
            session.add(task)
            session.flush()
            session.refresh(task)
            logger.info(f"Created download task: {task.id} ({music_id}) for job {job_id}")
            return task
        except Exception as e:
            logger.exception(f"Error creating download task: {str(e)}")
            return None
    
    def create_batch(self, session: Session, tasks_data: List[dict]) -> List[DownloadTask]:
        """
        Create multiple download tasks in batch.
        
        Args:
            session: Database session
            tasks_data: List of task data dictionaries
            
        Returns:
            List of created DownloadTask models
        """
        try:
            tasks = []
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
            session.flush()
            
            for task in tasks:
                session.refresh(task)
            
            logger.info(f"Created {len(tasks)} download tasks in batch")
            return tasks
        except Exception as e:
            logger.exception(f"Error creating tasks in batch: {str(e)}")
            return []
    
    def update(self, session: Session, task_id: int, **kwargs) -> Optional[DownloadTask]:
        """
        Update an existing download task.
        
        Args:
            session: Database session
            task_id: Task ID
            **kwargs: Fields to update
            
        Returns:
            Updated DownloadTask model or None if failed
        """
        try:
            task = session.query(DownloadTask).filter(
                DownloadTask.id == task_id
            ).first()
            
            if not task:
                logger.warning(f"Download task not found: {task_id}")
                return None
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            
            session.flush()
            session.refresh(task)
            logger.debug(f"Updated download task: {task_id}")
            return task
        except Exception as e:
            logger.exception(f"Error updating download task: {str(e)}")
            return None
    
    def update_progress(self, session: Session, task_id: int, progress_flag: int) -> Optional[DownloadTask]:
        """
        Update task progress by setting a flag.
        
        Args:
            session: Database session
            task_id: Task ID
            progress_flag: Progress flag to set
            
        Returns:
            Updated DownloadTask model or None if failed
        """
        try:
            task = session.query(DownloadTask).filter(
                DownloadTask.id == task_id
            ).first()
            
            if not task:
                logger.warning(f"Download task not found: {task_id}")
                return None
            
            # Set the progress flag
            task.progress_flags = task.progress_flags | progress_flag
            
            session.flush()
            session.refresh(task)
            logger.debug(f"Updated task progress: {task_id}, flag: {progress_flag}")
            return task
        except Exception as e:
            logger.exception(f"Error updating task progress: {str(e)}")
            return None
    
    def update_status(self, session: Session, task_id: int, status: str, 
                     error_message: str = None) -> Optional[DownloadTask]:
        """
        Update task status.
        
        Args:
            session: Database session
            task_id: Task ID
            status: New status
            error_message: Error message (optional)
            
        Returns:
            Updated DownloadTask model or None if failed
        """
        try:
            task = session.query(DownloadTask).filter(
                DownloadTask.id == task_id
            ).first()
            
            if not task:
                logger.warning(f"Download task not found: {task_id}")
                return None
            
            task.status = status
            if error_message is not None:
                task.error_message = error_message
            
            session.flush()
            session.refresh(task)
            logger.debug(f"Updated task status: {task_id} -> {status}")
            return task
        except Exception as e:
            logger.exception(f"Error updating task status: {str(e)}")
            return None
    
    
    def delete(self, session: Session, task_id: int) -> bool:
        """
        Delete a download task.
        
        Args:
            session: Database session
            task_id: Task ID
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            task = session.query(DownloadTask).filter(
                DownloadTask.id == task_id
            ).first()
            
            if not task:
                logger.warning(f"Download task not found: {task_id}")
                return False
            
            session.delete(task)
            logger.info(f"Deleted download task: {task_id}")
            return True
        except Exception as e:
            logger.exception(f"Error deleting download task: {str(e)}")
            return False
    
    def delete_by_job(self, session: Session, job_id: int) -> int:
        """
        Delete all tasks for a job.
        
        Args:
            session: Database session
            job_id: Job ID
            
        Returns:
            Number of deleted tasks
        """
        try:
            deleted_count = session.query(DownloadTask).filter(
                DownloadTask.job_id == job_id
            ).delete()
            
            logger.info(f"Deleted {deleted_count} tasks for job {job_id}")
            return deleted_count
        except Exception as e:
            logger.exception(f"Error deleting tasks by job: {str(e)}")
            return 0
