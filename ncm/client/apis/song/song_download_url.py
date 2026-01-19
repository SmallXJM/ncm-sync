"""Song download URL API - 获取歌曲下载链接"""

from typing import Union
from ncm.core.options import APIResponse, _create_options
from ncm.core.request import request
from ncm.infrastructure.http.decorators import ncm_api


@ncm_api("/api/song/download/url", ["GET", "POST"])
async def song_download_url(
        id: Union[str, int],
        br: int = 999000,
        **kwargs
) -> APIResponse:
    """
    获取客户端歌曲下载链接
    
    Args:
        id: 歌曲ID
        br: 音质，默认999000（无损）
        **kwargs: 其他参数
        
    Returns:
        APIResponse: 包含下载链接的响应
    """
    data = {
        'id': str(id),
        'br': int(br),
    }
    
    return await request("/api/song/enhance/download/url", data, _create_options(**kwargs))