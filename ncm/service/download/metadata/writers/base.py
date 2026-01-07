"""Base metadata writer class."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any


class BaseMetadataWriter(ABC):
    """基础元数据写入器类"""
    
    @abstractmethod
    def supports_format(self, file_format: str) -> bool:
        """
        检查是否支持指定格式
        
        Args:
            file_format: 文件格式
            
        Returns:
            是否支持该格式
        """
        pass
    
    @abstractmethod
    async def write_metadata(self, file_path: Path, metadata: Dict[str, Any]) -> bool:
        """
        写入元数据到文件
        
        Args:
            file_path: 文件路径
            metadata: 元数据字典
            
        Returns:
            写入是否成功
        """
        pass
    
    @abstractmethod
    async def write_artwork(self, file_path: Path, artwork_data: bytes) -> bool:
        """
        写入封面到文件
        
        Args:
            file_path: 文件路径
            artwork_data: 封面图片二进制数据
            
        Returns:
            写入是否成功
        """
        pass
    
    @abstractmethod
    async def write_lyrics(self, file_path: Path, lyrics_content: str) -> bool:
        """
        写入歌词到文件
        
        Args:
            file_path: 文件路径
            lyrics_content: 歌词内容
            
        Returns:
            写入是否成功
        """
        pass
    
    def _prepare_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        预处理元数据
        
        Args:
            metadata: 原始元数据
            
        Returns:
            处理后的元数据
        """
        # 基础预处理逻辑
        processed = {}
        
        # 基本信息
        if 'title' in metadata:
            processed['title'] = str(metadata['title'])
        if 'artist' in metadata:
            processed['artist'] = str(metadata['artist'])
        if 'artists' in metadata:
            processed['artists'] = metadata['artists']
        if 'album' in metadata:
            processed['album'] = str(metadata['album'])
        
        # 数字信息
        if 'cd_number' in metadata and metadata['cd_number']:
            processed['cd_number'] = str(metadata['cd_number'])
        if 'track_number' in metadata and metadata['track_number']:
            processed['track'] = str(metadata['track_number'])
        if 'publish_time' in metadata and metadata['publish_time']:
            # 转换时间戳为年份
            import datetime
            try:
                year = datetime.datetime.fromtimestamp(metadata['publish_time'] / 1000).year
                processed['date'] = str(year)
            except (ValueError, TypeError):
                pass
        
        # 歌词
        if 'sync_lyrics' in metadata:
            processed['lyrics'] = metadata['sync_lyrics']
        
        return processed