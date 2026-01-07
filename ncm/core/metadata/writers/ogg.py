"""OGG format metadata writer."""

from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from ncm.core.logging import get_logger
from .base import BaseMetadataWriter

logger = get_logger(__name__)

try:
    from mutagen.oggvorbis import OggVorbis
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    logger.warning("Mutagen not available for OGG writing")


class OGGWriter(BaseMetadataWriter):
    """OGG format metadata writer."""
    
    def supports_format(self, file_format: str) -> bool:
        """Check if this writer supports OGG format."""
        return file_format.lower() == '.ogg'
    
    async def write_metadata(self, file_path: Path, metadata: Dict[str, Any]) -> bool:
        """Write metadata to OGG file."""
        if not MUTAGEN_AVAILABLE:
            logger.warning("Mutagen not available, skipping OGG metadata writing")
            return False
        
        try:
            audio = OggVorbis(file_path)
            
            # Basic tags
            if metadata.get("title"):
                audio["TITLE"] = metadata["title"]
            
            if metadata.get("artist"):
                audio["ARTIST"] = metadata["artist"]
            
            if metadata.get("album"):
                audio["ALBUM"] = metadata["album"]
            
            # Album artist
            if metadata.get("artists") and isinstance(metadata["artists"], list):
                audio["ALBUMARTIST"] = ", ".join(metadata["artists"])
                audio["ARTIST"] = metadata["artists"]
            
            # Year from publish_time
            if metadata.get("publish_time"):
                try:
                    year = datetime.fromtimestamp(metadata["publish_time"] / 1000).year
                    audio["DATE"] = str(year)
                except (ValueError, TypeError):
                    pass
            
            # Track number
            if metadata.get("track_number"):
                audio["TRACKNUMBER"] = str(metadata["track_number"])
            
            # Disc number
            if metadata.get("cd_number"):
                try:
                    cd_num = metadata["cd_number"]
                    if isinstance(cd_num, str) and cd_num.isdigit():
                        audio["DISCNUMBER"] = cd_num
                    elif isinstance(cd_num, int):
                        audio["DISCNUMBER"] = str(cd_num)
                except (ValueError, TypeError):
                    pass
            
            # Synchronized lyrics
            if metadata.get("sync_lyrics"):
                audio["LYRICS"] = metadata["sync_lyrics"]
            
            audio.save()
            logger.info(f"Successfully wrote OGG metadata to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write OGG metadata: {str(e)}")
            return False