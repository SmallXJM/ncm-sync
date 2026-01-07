"""Base metadata writer class."""

import httpx
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional

from ncm.core.logging import get_logger

logger = get_logger(__name__)


class BaseMetadataWriter(ABC):
    """Base class for format-specific metadata writers."""
    
    def __init__(self):
        """Initialize base writer."""
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30),
            follow_redirects=True
        )
    
    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()
    
    @abstractmethod
    def supports_format(self, file_format: str) -> bool:
        """Check if this writer supports the given format."""
        pass
    
    @abstractmethod
    async def write_metadata(self, file_path: Path, metadata: Dict[str, Any]) -> bool:
        """Write metadata to audio file."""
        pass
    
    async def download_cover_art(self, url: str) -> Optional[bytes]:
        """Download album cover art."""
        if not url:
            return None
        
        try:
            response = await self.http_client.get(url)
            if response.status_code == 200:
                return response.content
            else:
                logger.warning(f"Failed to download cover art: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading cover art from {url}: {str(e)}")
            return None