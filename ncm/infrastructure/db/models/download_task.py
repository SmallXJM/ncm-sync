"""Download task model for tracking individual music download tasks."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint, ForeignKey
from ncm.infrastructure.db.engine import Base
from ncm.infrastructure.utils.time import UTC_CLOCK


class DownloadTask(Base):
    """Music download task - each task contains multiple data acquisition progress."""
    __tablename__ = 'download_task'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Music information (simple)
    music_id = Column(String, nullable=False, index=True)
    music_title = Column(String)
    music_artist = Column(String)
    music_album = Column(String)
    
    # Task configuration
    job_id = Column(Integer, ForeignKey('download_job.id'), nullable=False, index=True)
    
    # Quality information - only record actual quality obtained from server
    quality = Column(String)  # Actual music quality returned by server
    
    # Progress flags (using bit operations)
    progress_flags = Column(Integer, default=0, nullable=False)
    # Bit definitions - each flag represents an independent complete task:
    # 0x01 (1)  - Music file download completed (required)
    # 0x02 (2)  - Metadata task completed (fetch + embed + write as one task)
    # 0x04 (4)  - Cover task completed (fetch + embed + write as one task)
    # 0x08 (8)  - Lyrics task completed (fetch + embed + write as one task)
    # 0x10 (16) - File finalization completed (move to final location, required)
    
    # File information
    file_path = Column(String)  # 所处路径
    # file_path定义：
    # 1. 包含文件名
    # 2. status不为completed时，是下载中的临时路径。
    # 3. status为completed时，是以job.storage_path为基础的相对路径。
    file_name = Column(String)  # File name
    file_format = Column(String)  # 'mp3', 'flac', 'm4a'
    file_size = Column(Integer)  # File size in bytes
    
    # Status and error
    status = Column(String, default='pending', index=True)  
    # 'pending', 'downloading', 'processing', 'completed', 'failed', 'cancelled'
    error_message = Column(String)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: UTC_CLOCK.now())
    updated_at = Column(DateTime, default=lambda: UTC_CLOCK.now(), onupdate=lambda: UTC_CLOCK.now())
    started_at = Column(DateTime)  # Download start time
    completed_at = Column(DateTime)  # Completion time
    
    # Composite unique constraint: only one task per music per job
    __table_args__ = (
        UniqueConstraint('job_id', 'music_id', name='uq_job_music'),
    )
    
    @property
    def get_music_name(self) -> str:
        return f"歌曲 \"{self.file_name}\""
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'music_id': self.music_id,
            'music_title': self.music_title,
            'music_artist': self.music_artist,
            'music_album': self.music_album,
            'job_id': self.job_id,
            'quality': self.quality,
            'progress_flags': self.progress_flags,
            'file_path': self.file_path,
            'file_name': self.file_name,
            'file_format': self.file_format,
            'file_size': self.file_size,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }


class TaskProgress:
    """Task progress flag operations - each flag represents an independent complete task."""
    
    # === Independent complete tasks ===
    MUSIC_DOWNLOADED = 0x01        # Music file download completed (required)
    METADATA_COMPLETED = 0x02      # Metadata task completed (fetch + embed + write)
    COVER_COMPLETED = 0x04         # Cover task completed (fetch + embed + write)
    LYRICS_COMPLETED = 0x08        # Lyrics task completed (fetch + embed + write)
    FILE_FINALIZED = 0x10          # File finalization completed (move to final location)
    
    # === Required and optional tasks ===
    REQUIRED_FLAGS = MUSIC_DOWNLOADED | FILE_FINALIZED  # Music download and file finalization are required
    
    @staticmethod
    def has_flag(progress_flags: int, flag: int) -> bool:
        """Check if contains specified flag."""
        return (progress_flags & flag) != 0
    
    @staticmethod
    def set_flag(progress_flags: int, flag: int) -> int:
        """Set specified flag."""
        return progress_flags | flag
    
    @staticmethod
    def clear_flag(progress_flags: int, flag: int) -> int:
        """Clear specified flag."""
        return progress_flags & ~flag
    
    @staticmethod
    def is_music_ready(progress_flags: int) -> bool:
        """Check if music file is ready (music downloaded)."""
        return TaskProgress.has_flag(progress_flags, TaskProgress.MUSIC_DOWNLOADED)
    
    @staticmethod
    def is_fully_completed(progress_flags: int, job_config) -> bool:
        """Check if task is fully completed (according to job configuration)."""
        required = TaskProgress.REQUIRED_FLAGS
        
        # Add required tasks based on job configuration
        if job_config.embed_metadata:
            required |= TaskProgress.METADATA_COMPLETED
        if job_config.embed_cover:
            required |= TaskProgress.COVER_COMPLETED
        if job_config.embed_lyrics:
            required |= TaskProgress.LYRICS_COMPLETED
        
        return (progress_flags & required) == required
    
    @staticmethod
    def get_progress_summary(progress_flags: int) -> dict:
        """Get progress summary."""
        return {
            'music_downloaded': TaskProgress.has_flag(progress_flags, TaskProgress.MUSIC_DOWNLOADED),
            'metadata_completed': TaskProgress.has_flag(progress_flags, TaskProgress.METADATA_COMPLETED),
            'cover_completed': TaskProgress.has_flag(progress_flags, TaskProgress.COVER_COMPLETED),
            'lyrics_completed': TaskProgress.has_flag(progress_flags, TaskProgress.LYRICS_COMPLETED),
            'file_finalized': TaskProgress.has_flag(progress_flags, TaskProgress.FILE_FINALIZED),
        }
