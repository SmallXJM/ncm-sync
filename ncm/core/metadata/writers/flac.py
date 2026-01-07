"""FLAC format metadata writer."""

from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from ncm.core.logging import get_logger
from .base import BaseMetadataWriter

logger = get_logger(__name__)

try:
    from mutagen.flac import FLAC, Picture
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    logger.warning("Mutagen not available for FLAC writing")


class FLACWriter(BaseMetadataWriter):
    """FLAC format metadata writer."""
    
    def supports_format(self, file_format: str) -> bool:
        """Check if this writer supports FLAC format."""
        return file_format.lower() == '.flac'
    
    async def write_metadata(self, file_path: Path, metadata: Dict[str, Any]) -> bool:
        """Write metadata to FLAC file."""
        if not MUTAGEN_AVAILABLE:
            logger.warning("Mutagen not available, skipping FLAC metadata writing")
            return False
        
        try:
            audio = FLAC(file_path)
            
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
            
            # Technical metadata
            # 最好不要写入这些字段，FLAC 的真实参数来自 STREAMINFO
            # if metadata.get("sample_rate"):
            #     audio["SAMPLERATE"] = str(metadata["sample_rate"])
            
            # if metadata.get("bitrate"):
            #     audio["BITRATE"] = str(metadata["bitrate"])
            
            # if metadata.get("quality"):
            #     audio["QUALITY"] = metadata["quality"]
            
            #picture
            # Album artwork（主封面）
            pictures_to_write = []

            if metadata.get("album_pic"):
                cover_data = await self.download_cover_art(metadata["album_pic"])
                if cover_data:
                    picture = Picture()
                    picture.type = 3  # Cover (front)
                    picture.mime = 'image/jpeg'
                    picture.desc = 'Album cover'
                    picture.data = cover_data
                    pictures_to_write.append(picture)

            if pictures_to_write:
                audio.clear_pictures()
                for pic in pictures_to_write:
                    audio.add_picture(pic)
            
            # Synchronized lyrics
            if metadata.get("sync_lyrics"):
                audio["LYRICS"] = metadata["sync_lyrics"]
                logger.info(f"Writing SYNC field to FLAC: {len(metadata['sync_lyrics'])} characters")
            
            audio.save()
            logger.info(f"Successfully wrote FLAC metadata to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write FLAC metadata: {str(e)}")
            return False