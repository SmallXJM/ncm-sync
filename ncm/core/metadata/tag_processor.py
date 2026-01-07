"""Tag processor for handling metadata processing callbacks."""

import asyncio
from pathlib import Path
from typing import Dict, Any, Optional

from ncm.core.logging import get_logger
from .metadata_writer import MetadataWriter

logger = get_logger(__name__)


class TagProcessor:
    """Processes audio file tags after download completion."""
    
    def __init__(self):
        """Initialize tag processor."""
        self.metadata_writer = MetadataWriter()
        self._processing_tasks = set()
    
    async def close(self):
        """Close tag processor and cleanup resources."""
        # Wait for all processing tasks to complete
        if self._processing_tasks:
            logger.info(f"Waiting for {len(self._processing_tasks)} metadata processing tasks to complete...")
            await asyncio.gather(*self._processing_tasks, return_exceptions=True)
        
        await self.metadata_writer.close()
    
    def process_metadata_callback(self, task):
        """
        Callback function for processing metadata after download completion.
        
        Args:
            task: DownloadTask instance with metadata
        """
        # Create async task for metadata processing
        processing_task = asyncio.create_task(self._process_metadata_async(task))
        self._processing_tasks.add(processing_task)
        
        # Remove task from set when completed
        processing_task.add_done_callback(self._processing_tasks.discard)
    
    async def _process_metadata_async(self, task):
        """
        Asynchronously process metadata for a completed download.
        
        Args:
            task: DownloadTask instance
        """
        try:
            if not task.file_path.exists():
                logger.error(f"Downloaded file not found: {task.file_path}")
                return
            
            logger.info(f"Processing metadata for: {task.title}")
            
            # Prepare metadata for writing
            metadata_to_write = self._prepare_metadata(task)
            
            # Write metadata to file
            success = await self.metadata_writer.write_metadata(
                task.file_path, 
                metadata_to_write
            )
            
            if success:
                logger.info(f"Successfully processed metadata for: {task.title}")
            else:
                logger.warning(f"Failed to process metadata for: {task.title}")
                
        except Exception as e:
            logger.exception(f"Error processing metadata for {task.title}: {str(e)}")
    
    def _prepare_metadata(self, task) -> Dict[str, Any]:
        """
        Prepare metadata dictionary for writing to audio file.
        
        Args:
            task: DownloadTask instance
            
        Returns:
            Dictionary with prepared metadata
        """
        metadata = {}
        
        # Basic information
        metadata["title"] = task.title
        metadata["artist"] = task.artist
        
        # Extended metadata from task.metadata
        if task.metadata:
            # Album information
            metadata["album"] = task.metadata.get("album", "Unknown Album")
            metadata["album_pic"] = task.metadata.get("album_pic")
            
            # Artist information
            metadata["artists"] = task.metadata.get("artists", [task.artist])
            
            # Track information
            metadata["track_number"] = task.metadata.get("track_number", 0)
            metadata["cd_number"] = task.metadata.get("cd_number", "01")
            
            # Technical information
            metadata["duration"] = task.metadata.get("duration", 0)
            metadata["sample_rate"] = task.metadata.get("sample_rate", 44100)
            metadata["bitrate"] = task.bitrate
            metadata["quality"] = task.metadata.get("quality", "unknown")
            
            # Release information
            metadata["publish_time"] = task.metadata.get("publish_time", 0)
            
            # Synchronized lyrics (if available)
            if task.metadata.get("sync_lyrics"):
                metadata["sync_lyrics"] = task.metadata["sync_lyrics"]
                logger.info(f"Including sync lyrics in metadata: {len(metadata['sync_lyrics'])} characters")
            
            # Additional NCM-specific metadata
            metadata["music_id"] = task.music_id
            metadata["file_format"] = task.file_format
            metadata["file_size"] = task.file_size
            metadata["md5_hash"] = task.md5_hash
        
        return metadata
    
    def get_processing_status(self) -> Dict[str, Any]:
        """
        Get current processing status.
        
        Returns:
            Dictionary with processing statistics
        """
        return {
            "active_processing_tasks": len(self._processing_tasks),
            "metadata_writer_available": hasattr(self.metadata_writer, 'write_metadata')
        }