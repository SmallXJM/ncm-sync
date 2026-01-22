"""Song HTTP controller for music song functionality."""

import logging
from typing import List, Union
from ncm.client import APIResponse
from ncm.server.decorators import ncm_service
from ncm.service.cookie import with_cookie
from ncm.client.apis import song

logger = logging.getLogger(__name__)


class SongController:
    """HTTP controller for music song functionality."""

    def __init__(self):
        """Initialize song controller."""
        pass

    @ncm_service("/ncm/music/song/url_v1", ["GET", "POST"])
    @with_cookie(max_retries=2)
    async def song_url_v1(self,
                          id: Union[str, int],
                          level: str = "standard",
                          **kwargs
                          ) -> APIResponse:
        """
        获取歌曲链接 - v1

        Args:
            id: 歌曲ID
            level: 音质，默认standard, exhigh, lossless, hires, jyeffect(高清环绕声), sky(沉浸环绕声), jymaster(超清母带)
            **kwargs: 其他参数

        Returns:
            APIResponse: 包含下载链接的响应
        """
        resp = await song.url_v1(id=id, level=level, **kwargs)

        if not resp.success:
            return APIResponse(
                status=resp.status,
                body={
                    "code": resp.code,
                    "message": f"获取歌曲播放链接失败: {resp.message}",
                    "error": resp.body
                }
            )

        return resp

    @ncm_service("/ncm/music/song/detail", ["GET", "POST"])
    @with_cookie(max_retries=2)
    async def song_detail(self,
                          ids: Union[int, str, List[int], List[str]],
                          **kwargs
                          ) -> APIResponse:
        """
        批量获取歌曲的详细信息。

        :param ids: 歌曲 ID，可以是逗号分隔的字符串或 ID 列表。
        :returns: APIResponse 包含歌曲详情的列表。
        """
        resp = await song.detail(ids=ids, **kwargs)

        if not resp.success:
            return APIResponse(
                status=resp.status,
                body={
                    "code": resp.code,
                    "message": f"获取歌曲信息失败: {resp.message}",
                    "error": resp.body
                }
            )

        return resp


    @ncm_service("/ncm/music/song/lyric", ["GET", "POST"])
    @with_cookie(max_retries=2)
    async def song_lyric(self,
        id: Union[str, int],
                          **kwargs
                          ) -> APIResponse:
        """
        获取歌曲歌词
        
        Args:
            id: 歌曲ID
            **kwargs: 其他参数
            
        Returns:
            APIResponse: 包含歌词信息的响应
        """
        resp = await song.lyric(id=id, **kwargs)

        if not resp.success:
            return APIResponse(
                status=resp.status,
                body={
                    "code": resp.code,
                    "message": f"获取歌曲歌词失败: {resp.message}",
                    "error": resp.body
                }
            )

        return resp
