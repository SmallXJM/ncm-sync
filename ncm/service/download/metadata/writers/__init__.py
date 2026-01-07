"""Metadata writers package - maintains existing inheritance structure."""

from .mp3 import MP3Writer
from .flac import FLACWriter
from .mp4 import MP4Writer

# 写入器映射表
_WRITERS = {
    'mp3': MP3Writer(),
    'flac': FLACWriter(),
    'm4a': MP4Writer(),
    'mp4': MP4Writer(),
    'aac': MP4Writer(),
}


def get_writer_for_format(format_name: str):
    """
    根据格式获取对应的写入器
    
    Args:
        format_name: 文件格式名称
        
    Returns:
        对应的写入器实例，如果不支持则返回None
    """
    return _WRITERS.get(format_name.lower())


__all__ = ['MP3Writer', 'FLACWriter', 'MP4Writer', 'get_writer_for_format']