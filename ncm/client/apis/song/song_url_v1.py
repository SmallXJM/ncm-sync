"""
歌曲链接 - v1
此版本不再采用 br 作为音质区分的标准
而是采用 standard, exhigh, lossless, hires, jyeffect(高清环绕声), sky(沉浸环绕声), jymaster(超清母带) 进行音质判断
"""

from typing import Union
from ncm.client import APIResponse, _create_options
from ncm.client import request
from ncm.client.decorators import ncm_api


@ncm_api("/api/song/url/v1", ["GET", "POST"])
async def song_url_v1(
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
    data = {
        'ids': f"[{str(id)}]",
        'immerseType': 'c51',
        'level': level,
        'encodeType': 'flac',
    }
    
    return await request("/api/song/enhance/player/url/v1", data, _create_options(**kwargs))