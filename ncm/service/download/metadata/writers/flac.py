"""FLAC metadata writer implementation."""

from pathlib import Path
from typing import Dict, Any

from .base import BaseMetadataWriter
from ncm.core.logging import get_logger

logger = get_logger(__name__)


class FLACWriter(BaseMetadataWriter):
    """FLAC格式元数据写入器"""

    def supports_format(self, file_format: str) -> bool:
        """检查是否支持FLAC格式"""
        return file_format.lower() == 'flac'

    async def write_metadata(self, file_path: Path, metadata: Dict[str, Any]) -> bool:
        """写入FLAC元数据"""
        try:
            # 尝试导入mutagen
            try:
                from mutagen.flac import FLAC, Picture
            except ImportError:
                logger.warning("mutagen not available, skipping FLAC metadata writing")
                return True

            # 预处理元数据
            processed_metadata = self._prepare_metadata(metadata)

            # 加载FLAC文件
            audio_file = FLAC(str(file_path))

            # 写入基本信息
            if 'title' in processed_metadata:
                audio_file['TITLE'] = processed_metadata['title']

            if 'artists' in processed_metadata:
                audio_file['ARTIST'] = processed_metadata['artists']

            # 专辑艺术家有时候和歌手并不相同，但是该数据并不在song_detail内，后续看情况是否加入
            # audio_file['ALBUMARTIST'] = ", ".join(processed_metadata['artists'])

            if 'album' in processed_metadata:
                audio_file['ALBUM'] = processed_metadata['album']

            if 'date' in processed_metadata:
                audio_file['DATE'] = processed_metadata['date']

            if 'cd_number' in processed_metadata:
                audio_file["DISCNUMBER"] = processed_metadata['cd_number']

            if 'track' in processed_metadata:
                audio_file['TRACKNUMBER'] = processed_metadata['track']

            # # 写入歌词
            # if 'lyrics' in processed_metadata:
            #     audio_file['LYRICS'] = processed_metadata['lyrics']
            #
            # # 写入封面
            # if 'artwork' in metadata:
            #     try:
            #         artwork_data = metadata['artwork']
            #         picture = Picture()
            #         picture.type = 3  # Cover (front)
            #         picture.mime = 'image/jpeg'
            #         picture.desc = 'Cover'
            #         picture.data = artwork_data
            #         audio_file.add_picture(picture)
            #     except Exception as e:
            #         logger.warning(f"Failed to add artwork to FLAC: {e}")

            # 保存文件
            audio_file.save()

            logger.debug(f"FLAC metadata written successfully: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to write FLAC metadata for {file_path}: {e}")
            return False
    
    async def write_artwork(self, file_path: Path, artwork_data: bytes) -> bool:
        """写入封面到FLAC文件"""
        try:
            # 尝试导入mutagen
            try:
                from mutagen.flac import FLAC, Picture
            except ImportError:
                logger.warning("mutagen not available, skipping FLAC artwork writing")
                return True

            # 加载FLAC文件
            audio_file = FLAC(str(file_path))

            # 写入封面
            picture = Picture()
            picture.type = 3  # Cover (front)
            picture.mime = 'image/jpeg'
            picture.desc = 'Cover'
            picture.data = artwork_data
            audio_file.add_picture(picture)

            # 保存文件
            audio_file.save()

            logger.debug(f"FLAC artwork written successfully: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to write FLAC artwork for {file_path}: {e}")
            return False
    
    async def write_lyrics(self, file_path: Path, lyrics_content: str) -> bool:
        """写入歌词到FLAC文件"""
        try:
            # 尝试导入mutagen
            try:
                from mutagen.flac import FLAC
            except ImportError:
                logger.warning("mutagen not available, skipping FLAC lyrics writing")
                return True

            # 加载FLAC文件
            audio_file = FLAC(str(file_path))

            # 写入歌词
            audio_file['LYRICS'] = lyrics_content

            # 如果是LRC格式，也保存为SYNCEDLYRICS
            # if lyrics_content.strip().startswith('['):
            #     audio_file['SYNCEDLYRICS'] = lyrics_content

            # 保存文件
            audio_file.save()

            logger.debug(f"FLAC lyrics written successfully: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to write FLAC lyrics for {file_path}: {e}")
            return False
