"""MP3 metadata writer implementation."""

from pathlib import Path
from typing import Dict, Any, Optional, List

from mutagen.id3 import TPOS

from .base import BaseMetadataWriter
from ncm.core.logging import get_logger

logger = get_logger(__name__)


class MP3Writer(BaseMetadataWriter):
    """MP3格式元数据写入器"""
    
    def supports_format(self, file_format: str) -> bool:
        """检查是否支持MP3格式"""
        return file_format.lower() == 'mp3'
    
    async def write_metadata(self, file_path: Path, metadata: Dict[str, Any]) -> bool:
        """写入MP3元数据"""
        try:
            # 尝试导入mutagen
            try:
                from mutagen.mp3 import MP3
                from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TRCK, USLT, APIC
            except ImportError:
                logger.warning("mutagen not available, skipping MP3 metadata writing")
                return True
            
            # 预处理元数据
            processed_metadata = self._prepare_metadata(metadata)
            
            # 加载MP3文件
            audio_file = MP3(str(file_path))
            
            # 确保有ID3标签
            if audio_file.tags is None:
                audio_file.add_tags()
            
            # 写入基本信息
            if 'title' in processed_metadata:
                audio_file.tags.add(TIT2(encoding=3, text=processed_metadata['title']))
            
            if 'artist' in processed_metadata:
                audio_file.tags.add(TPE1(encoding=3, text=processed_metadata['artist']))
            
            if 'album' in processed_metadata:
                audio_file.tags.add(TALB(encoding=3, text=processed_metadata['album']))
            
            if 'date' in processed_metadata:
                audio_file.tags.add(TDRC(encoding=3, text=processed_metadata['date']))
            
            if 'track' in processed_metadata:
                audio_file.tags.add(TRCK(encoding=3, text=processed_metadata['track']))

            if 'cd_number' in processed_metadata:
                audio_file.tags.add(TPOS(encoding=3, text=processed_metadata['cd_number']))


            # # 写入歌词
            # if 'lyrics' in processed_metadata:
            #     audio_file.tags.add(USLT(encoding=3, lang='eng', desc='', text=processed_metadata['lyrics']))
            #
            # # 写入封面
            # if 'artwork' in metadata:
            #     try:
            #         artwork_data = metadata['artwork']
            #         audio_file.tags.add(APIC(
            #             encoding=3,
            #             mime='image/jpeg',
            #             type=3,  # Cover (front)
            #             desc='Cover',
            #             data=artwork_data
            #         ))
            #     except Exception as e:
            #         logger.warning(f"Failed to add artwork to MP3: {e}")
            
            # 保存文件
            audio_file.save()
            
            logger.debug(f"MP3 metadata written successfully: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write MP3 metadata for {file_path}: {e}")
            return False
    
    async def write_artwork(self, file_path: Path, artwork_data: bytes) -> bool:
        """写入封面到MP3文件"""
        try:
            # 尝试导入mutagen
            try:
                from mutagen.mp3 import MP3
                from mutagen.id3 import ID3, APIC
            except ImportError:
                logger.warning("mutagen not available, skipping MP3 artwork writing")
                return True
            
            # 加载MP3文件
            audio_file = MP3(str(file_path))
            
            # 确保有ID3标签
            if audio_file.tags is None:
                audio_file.add_tags()
            
            # 写入封面
            audio_file.tags.add(APIC(
                encoding=3,
                mime='image/jpeg',
                type=3,  # Cover (front)
                desc='Cover',
                data=artwork_data
            ))
            
            # 保存文件
            audio_file.save()
            
            logger.debug(f"MP3 artwork written successfully: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write MP3 artwork for {file_path}: {e}")
            return False
    
    async def write_lyrics(self, file_path: Path, lyrics_content: str) -> bool:
        """写入歌词到MP3文件"""
        try:
            # 尝试导入mutagen
            try:
                from mutagen.mp3 import MP3
                from mutagen.id3 import ID3, USLT, SYLT, Encoding
            except ImportError:
                logger.warning("mutagen not available, skipping MP3 lyrics writing")
                return True
            
            # 加载MP3文件
            audio_file = MP3(str(file_path))
            
            # 确保有ID3标签
            if audio_file.tags is None:
                audio_file.add_tags()
            
            # 写入非同步歌词
            # audio_file.tags.add(USLT(
            #     encoding=3,
            #     lang='eng',
            #     desc='',
            #     text=lyrics_content
            # ))
            
            # 如果是LRC格式，尝试解析并写入同步歌词
            if lyrics_content.strip().startswith('['):
                sylt_data = self._parse_lrc_to_sylt(lyrics_content)
                if sylt_data:
                    audio_file.tags.add(SYLT(
                        encoding=Encoding.UTF8,
                        lang='eng',
                        format=2,  # Absolute time, milliseconds
                        type=1,    # Lyrics
                        text=sylt_data
                    ))
            
            # 保存文件
            audio_file.save()
            
            logger.debug(f"MP3 lyrics written successfully: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write MP3 lyrics for {file_path}: {e}")
            return False
    
    def _parse_lrc_to_sylt(self, lrc_content: str) -> Optional[List[tuple]]:
        """将LRC格式转换为SYLT格式"""
        try:
            import re
            
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
                    text = match.group(4).strip()
                    
                    # 转换为毫秒
                    timestamp = (minutes * 60 + seconds) * 1000 + milliseconds
                    sylt_data.append((text, timestamp))
            
            return sylt_data if sylt_data else None
            
        except Exception as e:
            logger.warning(f"Failed to parse LRC to SYLT: {e}")
            return None