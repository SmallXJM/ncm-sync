"""Download task representation and management."""

import json
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse


class TaskStatus(Enum):
    """Download task status."""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    URL_EXPIRED = "url_expired"  # URL 过期，等待刷新


@dataclass
class DownloadSegment:
    """Represents a download segment/chunk."""
    start: int
    end: int
    downloaded: int = 0
    completed: bool = False
    
    @property
    def size(self) -> int:
        """Get segment size."""
        return self.end - self.start + 1
    
    @property
    def progress(self) -> float:
        """Get segment progress (0.0 to 1.0)."""
        return self.downloaded / self.size if self.size > 0 else 0.0


@dataclass
class DownloadTask:
    """Represents a download task."""
    
    # Essential download info only
    music_id: str
    url: str
    file_path: Path
    file_size: int
    md5_hash: str
    
    # Download config
    max_threads: int = 4
    chunk_size: int = 4 * 1024 * 1024  # 4MB chunks
    
    # Status
    status: TaskStatus = TaskStatus.PENDING
    downloaded_bytes: int = 0
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    # Internal
    segments: List[DownloadSegment] = None
    temp_dir: Optional[Path] = None
    resume_file: Optional[Path] = None

    def __init__(self, music_id: str, url: str, file_path: Path, file_size: int, md5_hash: str,
                 max_threads: int = 4, chunk_size: int = 4 * 1024 * 1024):
        """Initialize download task with required parameters."""
        self.music_id = music_id
        self.url = url
        self.file_path = file_path
        self.file_size = file_size
        self.md5_hash = md5_hash
        self.max_threads = max_threads
        self.chunk_size = chunk_size

        # Status fields
        self.status = TaskStatus.PENDING
        self.downloaded_bytes = 0
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.error_message = None

        # Internal fields
        self.segments = []
        self.temp_dir = None
        self.resume_file = None
        self.metadata = None

        # Initialize temp directory
        downloads_dir = Path("downloads")
        cache_dir = downloads_dir / ".cache"
        self.temp_dir = cache_dir / self.md5_hash
        self.resume_file = self.temp_dir / "resume.json"

    @property
    def progress(self) -> float:
        """Get overall progress (0.0 to 1.0)."""
        if self.file_size <= 0:
            return 0.0
        return self.downloaded_bytes / self.file_size
    
    @property
    def progress_percent(self) -> float:
        """Get progress as percentage."""
        return self.progress * 100
    
    @property
    def is_completed(self) -> bool:
        """Check if download is completed."""
        return self.status == TaskStatus.COMPLETED
    
    @property
    def is_active(self) -> bool:
        """Check if download is active."""
        return self.status in [TaskStatus.DOWNLOADING, TaskStatus.PENDING]
    
    def create_segments(self) -> List[DownloadSegment]:
        """Create download segments based on file size and thread count."""
        if self.file_size <= 0:
            return []
        
        segments = []
        segment_size = max(self.chunk_size, self.file_size // self.max_threads)
        
        start = 0
        while start < self.file_size:
            end = min(start + segment_size - 1, self.file_size - 1)
            segments.append(DownloadSegment(start=start, end=end))
            start = end + 1
        
        self.segments = segments
        return segments
    
    def get_segment_file_path(self, segment_index: int) -> Path:
        """Get file path for a specific segment."""
        segment = self.segments[segment_index]
        return self.temp_dir / f"{segment.start}-{segment.end}.part"
    
    def update_downloaded_bytes(self):
        """Update total downloaded bytes from segments."""
        self.downloaded_bytes = sum(seg.downloaded for seg in self.segments)
    
    def save_resume_info(self):
        """Save resume information to file."""
        if not self.temp_dir:
            return
            
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        resume_data = {
            "music_id": self.music_id,
            "url": self.url,
            "file_path": str(self.file_path),
            "file_size": self.file_size,
            "md5_hash": self.md5_hash,
            "status": self.status.value,
            "downloaded_bytes": self.downloaded_bytes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "segments": [
                {
                    "start": seg.start,
                    "end": seg.end,
                    "downloaded": seg.downloaded,
                    "completed": seg.completed
                }
                for seg in self.segments
            ]
        }
        
        with open(self.resume_file, 'w', encoding='utf-8') as f:
            json.dump(resume_data, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_resume_file(cls, resume_file: Path) -> Optional['DownloadTask']:
        """Load task from resume file."""
        try:
            with open(resume_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Create segments
            segments = []
            for seg_data in data.get("segments", []):
                segment = DownloadSegment(
                    start=seg_data["start"],
                    end=seg_data["end"],
                    downloaded=seg_data["downloaded"],
                    completed=seg_data["completed"]
                )
                segments.append(segment)
            
            # Create task
            task = cls(
                music_id=data["music_id"],
                url=data["url"],
                file_path=Path(data["file_path"]),
                file_size=data["file_size"],
                md5_hash=data["md5_hash"]
            )
            
            # Set additional fields
            task.status = TaskStatus(data["status"])
            task.downloaded_bytes = data["downloaded_bytes"]
            task.segments = segments
            
            # Set timestamps
            if data.get("created_at"):
                task.created_at = datetime.fromisoformat(data["created_at"])
            if data.get("started_at"):
                task.started_at = datetime.fromisoformat(data["started_at"])
            
            task.temp_dir = resume_file.parent
            task.resume_file = resume_file
            
            return task
            
        except Exception:
            return None
    
    def cleanup_temp_files(self):
        """Clean up temporary files."""
        if not self.temp_dir or not self.temp_dir.exists():
            return
            
        try:
            # Remove segment files
            for i in range(len(self.segments)):
                segment_file = self.get_segment_file_path(i)
                if segment_file.exists():
                    segment_file.unlink()
            
            # Remove resume file
            if self.resume_file and self.resume_file.exists():
                self.resume_file.unlink()
            
            # Remove temp directory if empty
            if self.temp_dir.exists() and not any(self.temp_dir.iterdir()):
                self.temp_dir.rmdir()
                
        except Exception:
            pass  # Ignore cleanup errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "music_id": self.music_id,
            "url": self.url,
            "file_path": str(self.file_path),
            "file_size": self.file_size,
            "md5_hash": self.md5_hash,
            "status": self.status.value,
            "progress": self.progress,
            "progress_percent": self.progress_percent,
            "downloaded_bytes": self.downloaded_bytes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message
        }