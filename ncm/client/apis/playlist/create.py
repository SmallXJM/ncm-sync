"""Playlist create API - 创建歌单"""

from typing import Union
from ncm.client import CryptoType, APIResponse, _create_options
from ncm.client import request
from ncm.client.decorators import ncm_api


@ncm_api("/api/playlist/create", ["GET","POST"])
async def playlist_create(
        name: str,
        privacy: Union[str, int] = 0,
        type: str = "NORMAL",
        **kwargs
) -> APIResponse:
    """
    创建歌单
    
    Args:
        name: 歌单名称
        privacy: 隐私设置，0为普通歌单，10为隐私歌单，默认0
        type: 歌单类型，NORMAL为普通歌单，VIDEO为视频歌单，SHARED为共享歌单，默认NORMAL
        **kwargs: 其他参数
        
    Returns:
        APIResponse: 包含创建结果的响应
    """
    data = {
        'name': name,
        'privacy': str(privacy),
        'type': type,
    }
    
    return await request("/api/playlist/create", data, _create_options(CryptoType.WEAPI, **kwargs))