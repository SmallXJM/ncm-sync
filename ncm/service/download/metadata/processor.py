"""Metadata processor implementation for new task-driven architecture."""

from pathlib import Path
from .writers import get_writer_for_format
from .fetchers import LyricsFetcher, ArtworkFetcher
from ncm.core.logging import get_logger
from ncm.service.download.service.async_task_service import AsyncTaskService
from ncm.service.download.models import DownloadTask as ServiceDownloadTask, get_task_cache_registry

logger = get_logger(__name__)


class MetadataProcessor:
    """元数据处理器 - 适配新的任务驱动架构"""
    
    def __init__(self):
        """初始化元数据处理器"""
        self.lyrics_fetcher = LyricsFetcher()
        self.artwork_fetcher = ArtworkFetcher()
        self.task_service = AsyncTaskService()
    
    async def process_metadata(self, task_id: int) -> bool:
        """
        处理元数据任务 (获取+嵌入+写入一体化)
        
        Args:
            task_id: 任务ID
            
        Returns:
            处理是否成功
        """
        try:
            logger.debug(f"Starting metadata processing for task {task_id}")
            
            task = await self.task_service.get_task(task_id)
            if not task:
                logger.error(f"Task not found: {task_id}")
                return False
            if not task.file_path or not Path(task.file_path).exists():
                logger.error(f"Audio file not found for metadata processing: {task_id}")
                return False
            
            # 获取并写入基础元数据
            success = await self._process_basic_metadata(task_id)
            
            if success:
                logger.debug(f"Metadata processing completed for task {task_id}")
            else:
                logger.warning(f"Metadata processing failed for task {task_id}")
            
            return success
            
        except Exception as e:
            logger.exception(f"Metadata processing failed for task {task_id}: {str(e)}")
            await self.task_service.update_fields(task_id, error_message=f"Metadata processing failed: {str(e)}")
            return False
    
    async def process_cover(self, task_id: int) -> bool:
        try:
            logger.debug(f"Starting cover processing for task {task_id}")
            task = await self.task_service.get_task(task_id)
            if not task:
                return False
            file_path = Path(task.file_path)
            if not file_path.exists():
                return False
            registry = get_task_cache_registry()
            cache = await registry.get_or_create(task.id, task.music_id)
            artwork_url = None
            if task.metadata and isinstance(task.metadata, dict):
                artwork_url = task.metadata.get("album_pic") or task.metadata.get("artwork_url")
            if not artwork_url and cache.song_detail:
                al = cache.song_detail.get("al") or {}
                artwork_url = al.get("picUrl") or None
            if not artwork_url:
                return True
            artwork_data = await self.artwork_fetcher.fetch(artwork_url)
            if not artwork_data:
                return True
            writer = get_writer_for_format(task.file_format)
            if writer:
                return await writer.write_artwork(file_path, artwork_data)
            return True
            
        except Exception as e:
            logger.exception(f"Cover processing failed for task {task_id}: {str(e)}")
            return False
    
    async def process_lyrics(self, task_id: int) -> bool:
        """
        处理歌词任务 (获取+嵌入+写入一体化)
        
        Args:
            task_id: 任务ID
            
        Returns:
            处理是否成功
        """
        try:
            logger.debug(f"Starting lyrics processing for task {task_id}")
            
            task = await self.task_service.get_task(task_id)
            if not task:
                return False
            
            # 获取歌词并嵌入文件
            success = await self._fetch_and_embed_lyrics(task_id)
            
            if success:
                logger.debug(f"Lyrics processing completed for task {task_id}")
            else:
                logger.warning(f"Lyrics processing failed for task {task_id}")
            
            return success
            
        except Exception as e:
            logger.exception(f"Lyrics processing failed for task {task_id}: {str(e)}")
            return False
    
    async def _process_basic_metadata(self, task_id: int) -> bool:
        try:
            task = await self.task_service.get_task(task_id)
            if not task:
                return False
            file_path = Path(task.file_path)
            if not file_path.exists():
                return False
            writer = get_writer_for_format(task.file_format)
            if not writer:
                return True
            registry = get_task_cache_registry()
            cache = await registry.get_or_create(task.id, task.music_id)
            service_task = ServiceDownloadTask(
                id=task.id,
                music_id=task.music_id,
                storage_location_id=getattr(task, "job_id", 0) or 0,
                quality=task.quality,
                custom_filename=getattr(task, "file_name", None),
                url=(cache.play_url or {}).get("url", ""),
                file_path=file_path,
                file_size=task.file_size or (cache.play_url or {}).get("size", 0),
                md5_hash=(cache.play_url or {}).get("md5", ""),
                status=task.status,
                metadata={}
            )
            title = getattr(task, "music_title", None)
            artist = getattr(task, "music_artist", None)
            album = getattr(task, "music_album", None)
            artists = []
            album_pic = ""
            duration = 0
            cd_number = "01"
            track_number = 0
            publish_time = 0
            if cache.song_detail:
                detail = cache.song_detail
                title = title or detail.get("name") or "Unknown"
                ar = detail.get("ar") or []
                artists = [a.get("name") for a in ar if isinstance(a, dict)]
                artist = artist or (", ".join(artists) if artists else "Unknown")
                al = detail.get("al") or {}
                album = album or al.get("name") or "Unknown Album"
                album_pic = al.get("picUrl") or ""
                duration = detail.get("dt", 0) or 0
                cd_number = str(detail.get("cd", "01"))
                track_number = detail.get("no", 0) or 0
                publish_time = detail.get("publishTime", 0) or 0
            bitrate = (cache.play_url or {}).get("br", 0)
            sample_rate = (cache.play_url or {}).get("sr", 0) or 44100
            file_format = task.file_format or (cache.play_url or {}).get("type", "mp3")
            metadata = {
                "title": title or "Unknown",
                "artist": artist or "Unknown",
                "artists": artists,
                "album": album or "Unknown Album",
                "album_pic": album_pic,
                "duration": duration,
                "cd_number": cd_number,
                "track_number": track_number,
                "publish_time": publish_time,
                "quality": task.quality,
                "file_format": file_format,
                "bitrate": bitrate,
                "sample_rate": sample_rate,
            }
            success = await writer.write_metadata(file_path, metadata)
            return success
        except Exception as e:
            logger.exception(f"Error processing basic metadata for task {task_id}: {str(e)}")
            return False
    
    async def _fetch_and_embed_artwork(self, task_id: int) -> bool:
        """获取并嵌入封面"""
        try:
            task = await self.task_service.get_task(task_id)
            if not task:
                return False
                
            file_path = Path(task.file_path)
            if not file_path.exists():
                return False
            
            # 从任务元数据中获取封面URL
            artwork_url = None
            if task.metadata and isinstance(task.metadata, dict):
                artwork_url = task.metadata.get('album_pic') or task.metadata.get('artwork_url')
            
            if not artwork_url:
                logger.warning(f"No artwork URL found for task {task_id}")
                return True  # 不阻止流程
            
            # 获取封面
            artwork_data = await self.artwork_fetcher.fetch(artwork_url)
            if not artwork_data:
                logger.warning(f"Failed to fetch artwork for task {task_id}")
                return True  # 不阻止流程
            
            # 获取写入器并嵌入封面
            writer = get_writer_for_format(task.file_format)
            if writer:
                success = await writer.write_artwork(file_path, artwork_data)
                return success
            
            return True
            
        except Exception as e:
            logger.exception(f"Error processing artwork for task {task_id}: {str(e)}")
            return False
    
    async def _fetch_and_embed_lyrics(self, task_id: int) -> bool:
        """获取并嵌入歌词"""
        try:
            task = await self.task_service.get_task(task_id)
            if not task:
                return False
            file_path = Path(task.file_path)
            if not file_path.exists():
                return False
            
            # 准备歌曲元数据用于歌词格式化
            song_metadata = {
                'title': task.music_title or 'Unknown',
                'artist': task.music_artist or 'Unknown',
                'album': task.music_album or 'Unknown Album'
            }
        
            # 获取歌词
            lyrics_content = await self.lyrics_fetcher.fetch_and_format_lyrics(task.music_id, song_metadata)
            if not lyrics_content:
                logger.warning(f"No lyrics found for music {task.music_id}")
                return True  # 不阻止流程

            # 获取写入器并嵌入歌词
            writer = get_writer_for_format(task.file_format)
            if writer:
                success = await writer.write_lyrics(file_path, lyrics_content)
                return success
            
            return True
            
        except Exception as e:
            logger.exception(f"Error processing lyrics for task {task_id}: {str(e)}")
            return False
    
    # 向后兼容方法 (用于旧的orchestrator调用)
    async def process(self, task_id: int) -> bool:
        """向后兼容的处理方法，实际调用process_metadata"""
        return await self.process_metadata(task_id)
    
    async def _fetch_lyrics(self, task):
        """获取歌词"""
        try:
            logger.debug(f"Fetching lyrics for task {task.id}")
            lyrics = await self.lyrics_fetcher.fetch_and_format_lyrics(task.music_id, task.metadata)
            if lyrics:
                task.metadata['sync_lyrics'] = lyrics
                logger.debug(f"Added lyrics to task {task.id}")
        except Exception as e:
            logger.warning(f"Failed to fetch lyrics for task {task.id}: {e}")
    
    async def _fetch_artwork(self, task):
        """获取封面"""
        try:
            artwork_url = task.metadata.get('album_pic')
            if artwork_url:
                logger.debug(f"Fetching artwork for task {task.id}")
                artwork_data = await self.artwork_fetcher.fetch(artwork_url)
                if artwork_data:
                    task.metadata['artwork'] = artwork_data
                    logger.debug(f"Added artwork to task {task.id}")
        except Exception as e:
            logger.warning(f"Failed to fetch artwork for task {task.id}: {e}")
    
    async def _write_metadata(self, task) -> bool:
        """写入元数据 - 使用现有的继承架构"""
        if not task.file_path or not task.file_path.exists():
            logger.warning(f"File not found for metadata writing: {task.file_path}")
            return False
        
        # 获取文件格式对应的写入器 (保持现有继承结构)
        file_format = task.file_path.suffix.lower().lstrip('.')
        writer = get_writer_for_format(file_format)
        
        if not writer:
            logger.warning(f"No metadata writer found for format: {file_format}")
            return True  # 不阻止流程继续
        
        try:
            logger.debug(f"Writing metadata for task {task.id} using {writer.__class__.__name__}")
            return await writer.write_metadata(task.file_path, task.metadata)
        except Exception as e:
            logger.error(f"Metadata writing failed for task {task.id}: {e}")
            return False
