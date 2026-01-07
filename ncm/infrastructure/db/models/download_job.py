"""Download job configuration model."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, UniqueConstraint
from ncm.infrastructure.db.engine import Base


class DownloadJob(Base):
    """Download job configuration for managing batch download tasks."""
    __tablename__ = 'download_job'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Job information
    job_name = Column(String, nullable=False)
    job_type = Column(String, nullable=False, index=True)  # 'playlist', 'album', 'artist', 'search', 'manual'
    
    # Source information
    source_type = Column(String, nullable=False)  # 'playlist', 'album', 'artist'
    source_id = Column(String, nullable=False, index=True)  # Playlist ID, Album ID, etc.
    source_owner_id = Column(String, index=True)  # Playlist owner ID
    source_name = Column(String)  # Playlist name, Album name, etc.
    
    # Storage configuration
    storage_path = Column(String, nullable=False)  # Storage directory
    filename_template = Column(String, default='{artist} - {title}')  # Filename template
    
    # Download configuration - simplified to single quality
    target_quality = Column(String, default='lossless')  # Target quality 'hires', 'lossless', 'standard'
    download_cover = Column(Boolean, default=True)  # Whether to download cover
    download_lyrics = Column(Boolean, default=True)  # Whether to download lyrics
    embed_metadata = Column(Boolean, default=True)  # Whether to embed metadata
    
    # Job status
    status = Column(String, default='created', index=True)
    # 'created', 'scanning', 'downloading', 'completed', 'failed', 'cancelled', 'paused'
    
    # Statistics
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)
    
    # Enable status
    enabled = Column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'job_name': self.job_name,
            'job_type': self.job_type,
            'source_type': self.source_type,
            'source_id': self.source_id,
            'source_owner_id': self.source_owner_id,
            'source_name': self.source_name,
            'storage_path': self.storage_path,
            'filename_template': self.filename_template,
            'target_quality': self.target_quality,
            'download_cover': self.download_cover,
            'download_lyrics': self.download_lyrics,
            'embed_metadata': self.embed_metadata,
            'status': self.status,
            'total_tasks': self.total_tasks,
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
