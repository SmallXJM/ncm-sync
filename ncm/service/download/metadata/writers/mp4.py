"""MP4/M4A metadata writer implementation."""

from pathlib import Path
from typing import Dict, Any

from .base import BaseMetadataWriter
from ncm.core.logging import get_logger

logger = get_logger(__name__)


class MP4Writer(BaseMetadataWriter):
    """MP4/M4A格式元数据写入器"""
    
    def supports_format(self, file_format: str) -> bool:
        """检查是否支持MP4/M4A格式"""
        return file_format.lower() in ['mp4', 'm4a', 'aac']
    
    async def write_metadata(self, file_path: Path, metadata: Dict[str, Any]) -> bool:
        """写入MP4/M4A元数据"""
        try:
            # 尝试导入mutagen
            try:
                from mutagen.mp4 import MP4, MP4Cover
            except ImportError:
                logger.warning("mutagen not available, skipping MP4 metadata writing")
                return True
            
            # 预处理元数据
            processed_metadata = self._prepare_metadata(metadata)
            
            # 加载MP4文件
            audio_file = MP4(str(file_path))
            
            # 写入基本信息
            if 'title' in processed_metadata:
                audio_file['\xa9nam'] = processed_metadata['title']
            
            if 'artist' in processed_metadata:
                audio_file['\xa9ART'] = processed_metadata['artist']
            
            if 'album' in processed_metadata:
                audio_file['\xa9alb'] = processed_metadata['album']
            
            if 'date' in processed_metadata:
                audio_file['\xa9day'] = processed_metadata['date']
            
            if 'track' in processed_metadata:
                try:
                    track_num = int(processed_metadata['track'])
                    audio_file['trkn'] = [(track_num, 0)]
                except (ValueError, TypeError):
                    pass
            
            # 写入歌词
            if 'lyrics' in processed_metadata:
                audio_file['\xa9lyr'] = processed_metadata['lyrics']
            
            # 写入封面
            if 'artwork' in metadata:
                try:
                    artwork_data = metadata['artwork']
                    audio_file['covr'] = [MP4Cover(artwork_data, MP4Cover.FORMAT_JPEG)]
                except Exception as e:
                    logger.warning(f"Failed to add artwork to MP4: {e}")
            
            # 保存文件
            audio_file.save()
            
            logger.debug(f"MP4 metadata written successfully: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write MP4 metadata for {file_path}: {e}")
            return False
    
    async def write_artwork(self, file_path: Path, artwork_data: bytes) -> bool:
        """写入封面到MP4文件"""
        try:
            # 尝试导入mutagen
            try:
                from mutagen.mp4 import MP4, MP4Cover
            except ImportError:
                logger.warning("mutagen not available, skipping MP4 artwork writing")
                return True
            
            # 加载MP4文件
            audio_file = MP4(str(file_path))
            
            # 写入封面
            audio_file['covr'] = [MP4Cover(artwork_data, MP4Cover.FORMAT_JPEG)]
            
            # 保存文件
            audio_file.save()
            
            logger.debug(f"MP4 artwork written successfully: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write MP4 artwork for {file_path}: {e}")
            return False
    
    async def write_lyrics(self, file_path: Path, lyrics_content: str) -> bool:
        """写入歌词到MP4文件"""
        try:
            # 尝试导入mutagen
            try:
                from mutagen.mp4 import MP4
            except ImportError:
                logger.warning("mutagen not available, skipping MP4 lyrics writing")
                return True
            
            # 加载MP4文件
            audio_file = MP4(str(file_path))
            
            # 写入歌词
            audio_file['\xa9lyr'] = lyrics_content
            
            # 保存文件
            audio_file.save()
            
            logger.debug(f"MP4 lyrics written successfully: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write MP4 lyrics for {file_path}: {e}")
            return False