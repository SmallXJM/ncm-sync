"""Unified metadata writer with callback-based format writers."""

from pathlib import Path
from typing import Dict, Any, List

from ncm.core.logging import get_logger
from .writers import MP3Writer, FLACWriter, MP4Writer, OGGWriter

logger = get_logger(__name__)


class MetadataWriter:
    """Unified metadata writer that delegates to format-specific writers."""
    
    def __init__(self):
        """Initialize metadata writer with format-specific writers."""
        self.writers = [
            MP3Writer(),
            FLACWriter(), 
            MP4Writer(),
            OGGWriter()
        ]
    
    async def close(self):
        """Close all writers."""
        for writer in self.writers:
            await writer.close()
    
    async def write_metadata(self, file_path: Path, metadata: Dict[str, Any]) -> bool:
        """
        Write metadata to audio file using appropriate format writer.
        
        Args:
            file_path: Path to audio file
            metadata: Metadata dictionary
            
        Returns:
            True if successful, False otherwise
        """
        if not file_path.exists():
            logger.error(f"Audio file not found: {file_path}")
            return False
        
        file_format = file_path.suffix.lower()
        
        # Find appropriate writer
        for writer in self.writers:
            if writer.supports_format(file_format):
                try:
                    return await writer.write_metadata(file_path, metadata)
                except Exception as e:
                    logger.exception(f"Failed to write metadata with {writer.__class__.__name__}: {str(e)}")
                    return False
        
        logger.warning(f"Unsupported audio format: {file_format}")
        return False