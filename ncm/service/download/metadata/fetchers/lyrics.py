"""Lyrics fetcher implementation."""
import re
from typing import Dict, Any, Optional, List
from ncm.core.logging import get_logger

logger = get_logger(__name__)


def get_lyrics_metadata(lyrics_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract lyrics metadata information.

    Args:
        lyrics_data: Raw lyrics data from API

    Returns:
        Dictionary with lyrics metadata
    """
    metadata = {}

    try:
        # Lyric user information
        lyric_user = lyrics_data.get("lyricUser", {})
        if lyric_user:
            metadata["lyric_author"] = lyric_user.get("nickname", "")
            metadata["lyric_author_id"] = lyric_user.get("userid", 0)

        # Translation user information
        trans_user = lyrics_data.get("transUser", {})
        if trans_user:
            metadata["translation_author"] = trans_user.get("nickname", "")
            metadata["translation_author_id"] = trans_user.get("userid", 0)

        # Check if translation exists
        tlyric_data = lyrics_data.get("tlyric", {})
        metadata["has_translation"] = bool(tlyric_data.get("lyric", ""))

        # Check if romanization exists
        romalrc_data = lyrics_data.get("romalrc", {})
        metadata["has_romanization"] = bool(romalrc_data.get("lyric", ""))

        return metadata

    except Exception as e:
        logger.exception(f"Error extracting lyrics metadata: {str(e)}")
        return {}


def extract_plain_lyrics(lyrics_data: Dict[str, Any]) -> Optional[str]:
    """
    Extract plain text lyrics (without timestamps) from lyrics data.

    Args:
        lyrics_data: Raw lyrics data from API

    Returns:
        Plain text lyrics or None if failed
    """
    try:
        # Extract main LRC lyrics
        lrc_data = lyrics_data.get("lrc", {})
        lrc_lyric = lrc_data.get("lyric", "")

        if not lrc_lyric:
            return None

        # Parse and extract only the text content
        lyrics_lines = []
        lrc_pattern = r'\[(\d{2}:\d{2}\.\d{2,3})\](.*)'

        for line in lrc_lyric.split('\n'):
            line = line.strip()
            if not line:
                continue

            match = re.match(lrc_pattern, line)
            if match:
                lyric_text = match.group(2).strip()
                if lyric_text:  # Skip empty lines
                    lyrics_lines.append(lyric_text)

        return "\n".join(lyrics_lines) if lyrics_lines else None

    except Exception as e:
        logger.exception(f"Error extracting plain lyrics: {str(e)}")
        return None


def _parse_lrc_lines(lrc_content: str) -> Dict[str, str]:
    """
    Parse LRC content into timestamp -> lyric mapping.

    Args:
        lrc_content: Raw LRC content string

    Returns:
        Dictionary mapping timestamps to lyrics
    """
    lyrics = {}

    if not lrc_content:
        return lyrics

    # LRC format: [mm:ss.xx]lyric text
    lrc_pattern = r'\[(\d{2}:\d{2}\.\d{2,3})\](.*)'

    for line in lrc_content.split('\n'):
        line = line.strip()
        if not line:
            continue

        match = re.match(lrc_pattern, line)
        if match:
            timestamp = match.group(1)
            lyric_text = match.group(2).strip()

            # Normalize timestamp format (ensure 3 digits for milliseconds)
            if len(timestamp.split('.')[-1]) == 2:
                timestamp += '0'

            lyrics[timestamp] = lyric_text

    return lyrics


def extract_lrc_content(lyrics_data: Dict[str, Any], song_metadata: Dict[str, Any]) -> Optional[str]:
    """
    Extract and format LRC content from lyrics data (original lyrics only).

    Args:
        lyrics_data: Raw lyrics data from API
        song_metadata: Song metadata for header information

    Returns:
        Formatted LRC content string or None
    """
    try:
        title = song_metadata.get('title', 'Unknown')
        artist = song_metadata.get('artist', 'Unknown')
        album = song_metadata.get('album', 'Unknown Album')

        logger.debug(f"Extracting LRC content for: {title}")

        # Extract main LRC lyrics only (no translation)
        lrc_data = lyrics_data.get("lrc", {})
        lrc_lyric = lrc_data.get("lyric", "")

        logger.debug(f"Raw LRC lyric length: {len(lrc_lyric) if lrc_lyric else 0}")

        if not lrc_lyric:
            logger.warning("No LRC lyrics found in response")
            return None

        # Extract lyric user info
        lyric_user = lyrics_data.get("lyricUser", {})

        # Build LRC content
        lrc_lines = []

        # Add metadata header
        lrc_lines.append(f"[ti:{title}]")
        lrc_lines.append(f"[ar:{artist}]")
        lrc_lines.append(f"[al:{album}]")

        # Add lyric author information
        if lyric_user and lyric_user.get("nickname"):
            lrc_lines.append(f"[by:{lyric_user['nickname']}]")

        # Add tool info
        lrc_lines.append("[tool:ncm-sync]")
        lrc_lines.append("")

        # Process main lyrics only
        main_lyrics = _parse_lrc_lines(lrc_lyric)
        logger.debug(f"Parsed main lyrics: {len(main_lyrics)} lines")

        # Add lyrics to content (sorted by timestamp)
        for timestamp, content in sorted(main_lyrics.items()):
            if content.strip():  # Skip empty lines
                lrc_lines.append(f"[{timestamp}]{content}")

        final_content = "\n".join(lrc_lines)
        logger.debug(f"Final LRC content length: {len(final_content)}")

        return final_content

    except Exception as e:
        logger.exception(f"Error extracting LRC content: {str(e)}")
        return None


class LyricsFetcher:
    """歌词获取器"""

    def __init__(self):
        """初始化歌词获取器"""
        self._song_controller = None

    @property
    def song_controller(self):
        """懒加载歌词控制器"""
        if self._song_controller is None:
            from ncm.api.ncm.music.song import SongController
            self._song_controller = SongController()
        return self._song_controller

    async def fetch_lyrics(self, music_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch lyrics data from NCM API.
        
        Args:
            music_id: Music ID to fetch lyrics for
            
        Returns:
            Lyrics data dictionary or None if failed
        """
        try:
            logger.debug(f"Fetching lyrics for music ID: {music_id}")
            response = await self.song_controller.song_lyric(id=music_id)

            if not response.success:
                logger.debug(f"Failed to fetch lyrics for music ID {music_id}: {response.body}")
                return None

            return response.body

        except Exception as e:
            logger.exception(f"Error fetching lyrics for music ID {music_id}: {str(e)}")
            return None

    async def fetch_and_format_lyrics(self, music_id: str, song_metadata: Dict[str, Any]) -> Optional[str]:
        """
        Fetch lyrics from API and format as LRC content.
        
        Args:
            music_id: Music ID to fetch lyrics for
            song_metadata: Song metadata for header information
            
        Returns:
            Formatted LRC content string or None if failed
        """
        try:
            # Fetch lyrics data
            lyrics_data = await self.fetch_lyrics(music_id)
            if not lyrics_data:
                logger.warning(f"No lyrics available for music ID: {music_id}")
                return None

            # Extract and format LRC content
            lrc_content = extract_lrc_content(lyrics_data, song_metadata)
            if not lrc_content:
                logger.warning(f"No valid LRC content for music ID: {music_id}")
                return None

            logger.debug(f"Successfully formatted lyrics for music ID: {music_id}")
            return lrc_content

        except Exception as e:
            logger.exception(f"Error fetching and formatting lyrics for music ID {music_id}: {str(e)}")
            return None
