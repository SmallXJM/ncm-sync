"""Artwork fetcher implementation."""

import httpx
from typing import Optional
from ncm.core.logging import get_logger

logger = get_logger(__name__)


class ArtworkFetcher:
    """封面图片获取器"""
    
    def __init__(self):
        """初始化封面获取器"""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            follow_redirects=True
        )
    
    async def fetch(self, artwork_url: str) -> Optional[bytes]:
        """
        获取封面图片数据
        
        Args:
            artwork_url: 封面图片URL
            
        Returns:
            图片二进制数据，如果获取失败则返回None
        """
        if not artwork_url:
            return None
        
        try:
            logger.debug(f"Fetching artwork from: {artwork_url}")
            
            # 添加用户代理头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = await self._client.get(artwork_url, headers=headers)
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch artwork: HTTP {response.status_code}")
                return None
            
            # 检查内容类型
            content_type = response.headers.get('content-type', '').lower()
            if not content_type.startswith('image/'):
                logger.warning(f"Invalid content type for artwork: {content_type}")
                return None
            
            artwork_data = response.content
            logger.debug(f"Successfully fetched artwork: {len(artwork_data)} bytes")
            return artwork_data
            
        except Exception as e:
            logger.warning(f"Error fetching artwork from {artwork_url}: {e}")
            return None
    
    async def close(self):
        """关闭HTTP客户端"""
        await self._client.aclose()