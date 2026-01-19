"""User playlist API - 用户歌单列表"""

from typing import Union
from ncm.client import CryptoType, APIResponse, _create_options
from ncm.client import request
from ncm.infrastructure.http.decorators import ncm_api


@ncm_api("/api/user/playlist", ["GET", "POST"])
async def user_playlist(
        uid: Union[str, int],
        limit: int = 30,
        offset: int = 0,
        include_video: bool = True,
        **kwargs
) -> APIResponse:
    """
    获取用户歌单列表
    
    Args:
        uid: 用户ID
        limit: 返回数量限制，默认30
        offset: 偏移量，默认0
        include_video: 是否包含视频，默认True
        **kwargs: 其他参数
        
    Returns:
        APIResponse: 包含用户歌单列表的响应
    """
    data = {
        'uid': str(uid),
        'limit': limit,
        'offset': offset,
        'includeVideo': include_video,
    }
    
    return await request("/api/user/playlist", data, _create_options(CryptoType.WEAPI, **kwargs))