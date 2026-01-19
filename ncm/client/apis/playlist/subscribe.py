"""Playlist subscribe API - 收藏/取消收藏歌单"""

from typing import Union
from ncm.client import CryptoType, APIResponse, _create_options
from ncm.client import request
from ncm.api import ncm_api


@ncm_api("/api/playlist/subscribe", ["GET","POST"])
async def playlist_subscribe(
        id: Union[str, int],
        t: Union[str, int],
        check_token: str = None,
        **kwargs
) -> APIResponse:
    """
    收藏或取消收藏歌单
    
    Args:
        id: 歌单ID
        t: 操作类型，1为收藏，其他为取消收藏
        check_token: 检查令牌，收藏时需要
        **kwargs: 其他参数
        
    Returns:
        APIResponse: 包含操作结果的响应
    """
    # 根据操作类型确定路径
    path = "subscribe" if str(t) == "1" else "unsubscribe"
    
    data = {
        'id': str(id),
    }
    
    # 收藏时添加 checkToken
    if str(t) == "1" and check_token:
        data['checkToken'] = check_token
    
    # 强制开启 checkToken
    kwargs['checkToken'] = True
    
    return await request(f"/api/playlist/{path}", data, _create_options(CryptoType.EAPI, **kwargs))