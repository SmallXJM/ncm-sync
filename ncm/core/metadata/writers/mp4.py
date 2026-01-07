"""MP4/M4A format metadata writer."""

from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from ncm.core.logging import get_logger
from .base import BaseMetadataWriter

logger = get_logger(__name__)

try:
    from mutagen.mp4 import MP4, MP4Cover
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    logger.warning("Mutagen not available for MP4 writing")


class MP4Writer(BaseMetadataWriter):
    """MP4/M4A format metadata writer."""
    
    def supports_format(self, file_format: str) -> bool:
        """Check if this writer supports MP4/M4A format."""
        return file_format.lower() in ['.m4a', '.mp4', '.aac']
    
    async def write_metadata(self, file_path: Path, metadata: Dict[str, Any]) -> bool:
        """Write metadata to MP4/M4A file."""
        if not MUTAGEN_AVAILABLE:
            logger.warning("Mutagen not available, skipping MP4 metadata writing")
            return False
        
        try:
            audio = MP4(file_path)
            
            # Basic tags
            if metadata.get("title"):
                audio["\xa9nam"] = metadata["title"]
            
            if metadata.get("artist"):
                audio["\xa9ART"] = metadata["artist"]
            
            if metadata.get("album"):
                audio["\xa9alb"] = metadata["album"]
            
            # Album artist
            if metadata.get("artists") and isinstance(metadata["artists"], list):
                audio["aART"] = ", ".join(metadata["artists"])
            
            # Year from publish_time
            if metadata.get("publish_time"):
                try:
                    year = datetime.fromtimestamp(metadata["publish_time"] / 1000).year
                    audio["\xa9day"] = str(year)
                except (ValueError, TypeError):
                    pass
            
            # Track number
            if metadata.get("track_number"):
                audio["trkn"] = [(metadata["track_number"], 0)]
            
            # Disc number
            if metadata.get("cd_number"):
                try:
                    cd_num = metadata["cd_number"]
                    if isinstance(cd_num, str) and cd_num.isdigit():
                        audio["disk"] = [(int(cd_num), 0)]
                    elif isinstance(cd_num, int):
                        audio["disk"] = [(cd_num, 0)]
                except (ValueError, TypeError):
                    pass
            
            # Album artwork
            if metadata.get("album_pic"):
                cover_data = await self.download_cover_art(metadata["album_pic"])
                if cover_data:
                    audio["covr"] = [MP4Cover(cover_data, MP4Cover.FORMAT_JPEG)]
            
            # Synchronized lyrics
            if metadata.get("sync_lyrics"):
                audio["----:com.apple.iTunes:LYRICS"] = metadata["sync_lyrics"].encode('utf-8')
            
            audio.save()
            logger.info(f"Successfully wrote MP4 metadata to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write MP4 metadata: {str(e)}")
            return False