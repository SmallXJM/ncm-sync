"""MP3 format metadata writer."""

import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from ncm.core.logging import get_logger
from .base import BaseMetadataWriter

logger = get_logger(__name__)

try:
    from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TRCK, TPOS, TPE2, APIC, SYLT
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    logger.warning("Mutagen not available for MP3 writing")


class MP3Writer(BaseMetadataWriter):
    """MP3 format metadata writer."""
    
    def supports_format(self, file_format: str) -> bool:
        """Check if this writer supports MP3 format."""
        return file_format.lower() == '.mp3'
    
    async def write_metadata(self, file_path: Path, metadata: Dict[str, Any]) -> bool:
        """Write metadata to MP3 file."""
        if not MUTAGEN_AVAILABLE:
            logger.warning("Mutagen not available, skipping MP3 metadata writing")
            return False
        
        try:
            audio = ID3(file_path)
            
            # Basic tags
            if metadata.get("title"):
                audio.add(TIT2(encoding=3, text=metadata["title"]))
            
            if metadata.get("artist"):
                audio.add(TPE1(encoding=3, text=metadata["artist"]))
            
            if metadata.get("album"):
                audio.add(TALB(encoding=3, text=metadata["album"]))
            
            # Album artist
            if metadata.get("artists") and isinstance(metadata["artists"], list):
                album_artist = ", ".join(metadata["artists"])
                audio.add(TPE2(encoding=3, text=album_artist))
            
            # Year from publish_time
            if metadata.get("publish_time"):
                try:
                    year = datetime.fromtimestamp(metadata["publish_time"] / 1000).year
                    audio.add(TDRC(encoding=3, text=str(year)))
                except (ValueError, TypeError):
                    pass
            
            # Track number
            if metadata.get("track_number"):
                audio.add(TRCK(encoding=3, text=str(metadata["track_number"])))
            
            # Disc number
            if metadata.get("cd_number"):
                try:
                    cd_num = metadata["cd_number"]
                    if isinstance(cd_num, str) and cd_num.isdigit():
                        audio.add(TPOS(encoding=3, text=cd_num))
                    elif isinstance(cd_num, int):
                        audio.add(TPOS(encoding=3, text=str(cd_num)))
                except (ValueError, TypeError):
                    pass
            
            # Album artwork
            if metadata.get("album_pic"):
                cover_data = await self.download_cover_art(metadata["album_pic"])
                if cover_data:
                    audio.add(APIC(
                        encoding=3,
                        mime='image/jpeg',
                        type=3,  # Cover (front)
                        desc='Cover',
                        data=cover_data
                    ))
            
            # Synchronized lyrics
            if metadata.get("sync_lyrics"):
                sylt_data = self._parse_lrc_to_sylt(metadata["sync_lyrics"])
                if sylt_data:
                    audio.add(SYLT(
                        encoding=3,
                        lang='eng',
                        format=2,  # Absolute time in milliseconds
                        type=1,    # Lyrics
                        desc='Synchronized Lyrics',
                        text=sylt_data
                    ))
            
            audio.save()
            logger.info(f"Successfully wrote MP3 metadata to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write MP3 metadata: {str(e)}")
            return False
    
    def _parse_lrc_to_sylt(self, lrc_content: str) -> Optional[List[tuple]]:
        """Parse LRC format to SYLT format for ID3."""
        if not lrc_content:
            return None
        
        sylt_data = []
        lrc_pattern = r'\[(\d{2}):(\d{2})\.(\d{2,3})\](.*)'
        
        for line in lrc_content.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            match = re.match(lrc_pattern, line)
            if match:
                minutes = int(match.group(1))
                seconds = int(match.group(2))
                milliseconds = int(match.group(3).ljust(3, '0')[:3])
                lyric_text = match.group(4).strip()
                
                timestamp_ms = (minutes * 60 + seconds) * 1000 + milliseconds
                
                if lyric_text and not lyric_text.startswith(('[ti:', '[ar:', '[al:', '[by:', '[tool:')):
                    sylt_data.append((lyric_text, timestamp_ms))
        
        return sylt_data if sylt_data else None