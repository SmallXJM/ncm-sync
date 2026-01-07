"""Lyric API - 歌词获取"""

from typing import Union
from ncm.core.options import CryptoType, APIResponse, _create_options
from ncm.core.request import request
from ncm.infrastructure.http.decorators import ncm_api


@ncm_api("/api/lyric", ["GET", "POST"])
async def lyric(
        id: Union[str, int],
        **kwargs
) -> APIResponse:
    """
    获取歌曲歌词
    
    Args:
        id: 歌曲ID
        tv: 翻译版本，默认-1
        lv: 歌词版本，默认-1
        rv: 罗马音版本，默认-1
        kv: 卡拉OK版本，默认-1
        **kwargs: 其他参数
        
    Returns:
        APIResponse: 包含歌词信息的响应
    """
    data = {
        'id': str(id),
        'tv': -1,
        'lv': -1,
        'rv': -1,
        'kv': -1,
        '_nmclfl': 1,
    }
    
    return await request("/api/song/lyric", data, _create_options(CryptoType.WEAPI, **kwargs))


@ncm_api("/api/lyric_new", ["GET", "POST"])
async def lyric_new(
        id: Union[str, int],
        **kwargs
) -> APIResponse:
    """
    新版歌词 - 包含逐字歌词

    Args:
        id: 歌曲ID
        **kwargs: 其他参数

    Returns:
        APIResponse: 包含歌词信息的响应
    """
    data = {
        'id': str(id),
        'cp': False,
        'tv': 0,
        'lv': 0,
        'rv': 0,
        'kv': 0,
        'yv': 0,
        'ytv': 0,
        'yrv': 0,
    }

    return await request("/api/song/lyric/v1", data, _create_options(CryptoType.WEAPI, **kwargs))