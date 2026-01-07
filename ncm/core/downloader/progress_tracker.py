"""Download progress tracking and speed calculation."""

import time
from collections import deque
from dataclasses import dataclass
from threading import Lock
from typing import Dict, Optional, Deque, Tuple


@dataclass
class SpeedSample:
    """Speed measurement sample."""
    timestamp: float
    bytes_downloaded: int


class ProgressTracker:
    """Tracks download progress and calculates real-time speed."""
    
    def __init__(self, window_size: int = 10):
        """
        Initialize progress tracker.
        
        Args:
            window_size: Number of samples to keep for speed calculation
        """
        self.window_size = window_size
        self._lock = Lock()
        
        # Per-task tracking
        self._task_samples: Dict[str, Deque[SpeedSample]] = {}
        self._task_total_bytes: Dict[str, int] = {}
        self._task_start_time: Dict[str, float] = {}
        
        # Global tracking
        self._global_samples: Deque[SpeedSample] = deque(maxlen=window_size)
        self._global_total_bytes = 0
        self._global_start_time = time.time()
    
    def start_task(self, task_id: str):
        """Start tracking a task."""
        with self._lock:
            self._task_samples[task_id] = deque(maxlen=self.window_size)
            self._task_total_bytes[task_id] = 0
            self._task_start_time[task_id] = time.time()
    
    def update_task_progress(self, task_id: str, bytes_downloaded: int):
        """Update task progress."""
        current_time = time.time()
        
        with self._lock:
            if task_id not in self._task_samples:
                self.start_task(task_id)
            
            # Update task tracking
            old_bytes = self._task_total_bytes.get(task_id, 0)
            self._task_total_bytes[task_id] = bytes_downloaded
            
            sample = SpeedSample(current_time, bytes_downloaded)
            self._task_samples[task_id].append(sample)
            
            # Update global tracking
            bytes_diff = bytes_downloaded - old_bytes
            self._global_total_bytes += bytes_diff
            
            global_sample = SpeedSample(current_time, self._global_total_bytes)
            self._global_samples.append(global_sample)
    
    def get_task_speed(self, task_id: str) -> float:
        """Get current download speed for a task (bytes/second)."""
        with self._lock:
            samples = self._task_samples.get(task_id)
            if not samples or len(samples) < 2:
                return 0.0
            
            # Calculate speed from recent samples
            recent_samples = list(samples)[-min(5, len(samples)):]
            if len(recent_samples) < 2:
                return 0.0
            
            time_diff = recent_samples[-1].timestamp - recent_samples[0].timestamp
            bytes_diff = recent_samples[-1].bytes_downloaded - recent_samples[0].bytes_downloaded
            
            if time_diff <= 0:
                return 0.0
            
            return bytes_diff / time_diff
    
    def get_task_average_speed(self, task_id: str) -> float:
        """Get average download speed for a task since start."""
        with self._lock:
            if task_id not in self._task_start_time or task_id not in self._task_total_bytes:
                return 0.0
            
            elapsed = time.time() - self._task_start_time[task_id]
            total_bytes = self._task_total_bytes[task_id]
            
            if elapsed <= 0:
                return 0.0
            
            return total_bytes / elapsed
    
    def get_global_speed(self) -> float:
        """Get current global download speed (bytes/second)."""
        with self._lock:
            if len(self._global_samples) < 2:
                return 0.0
            
            # Calculate speed from recent samples
            recent_samples = list(self._global_samples)[-min(5, len(self._global_samples)):]
            if len(recent_samples) < 2:
                return 0.0
            
            time_diff = recent_samples[-1].timestamp - recent_samples[0].timestamp
            bytes_diff = recent_samples[-1].bytes_downloaded - recent_samples[0].bytes_downloaded
            
            if time_diff <= 0:
                return 0.0
            
            return bytes_diff / time_diff
    
    def get_global_average_speed(self) -> float:
        """Get average global download speed since start."""
        with self._lock:
            elapsed = time.time() - self._global_start_time
            if elapsed <= 0:
                return 0.0
            
            return self._global_total_bytes / elapsed
    
    def finish_task(self, task_id: str):
        """Finish tracking a task."""
        with self._lock:
            # Keep the data for statistics, just mark as finished
            # Could add a finished_tasks set if needed
            pass
    
    def remove_task(self, task_id: str):
        """Remove task from tracking."""
        with self._lock:
            self._task_samples.pop(task_id, None)
            self._task_total_bytes.pop(task_id, None)
            self._task_start_time.pop(task_id, None)
    
    def get_task_stats(self, task_id: str) -> Dict[str, float]:
        """Get comprehensive stats for a task."""
        return {
            "current_speed": self.get_task_speed(task_id),
            "average_speed": self.get_task_average_speed(task_id),
            "total_bytes": self._task_total_bytes.get(task_id, 0),
            "elapsed_time": time.time() - self._task_start_time.get(task_id, time.time())
        }
    
    def get_global_stats(self) -> Dict[str, float]:
        """Get comprehensive global stats."""
        return {
            "current_speed": self.get_global_speed(),
            "average_speed": self.get_global_average_speed(),
            "total_bytes": self._global_total_bytes,
            "elapsed_time": time.time() - self._global_start_time,
            "active_tasks": len(self._task_samples)
        }
    
    @staticmethod
    def format_speed(bytes_per_second: float) -> str:
        """Format speed in human readable format."""
        if bytes_per_second < 1024:
            return f"{bytes_per_second:.1f} B/s"
        elif bytes_per_second < 1024 * 1024:
            return f"{bytes_per_second / 1024:.1f} KB/s"
        elif bytes_per_second < 1024 * 1024 * 1024:
            return f"{bytes_per_second / (1024 * 1024):.1f} MB/s"
        else:
            return f"{bytes_per_second / (1024 * 1024 * 1024):.1f} GB/s"
    
    @staticmethod
    def format_size(bytes_size: int) -> str:
        """Format size in human readable format."""
        if bytes_size < 1024:
            return f"{bytes_size} B"
        elif bytes_size < 1024 * 1024:
            return f"{bytes_size / 1024:.1f} KB"
        elif bytes_size < 1024 * 1024 * 1024:
            return f"{bytes_size / (1024 * 1024):.1f} MB"
        else:
            return f"{bytes_size / (1024 * 1024 * 1024):.1f} GB"