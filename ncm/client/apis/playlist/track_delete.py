"""Playlist track delete API - 从歌单删除歌曲"""

from typing import Union, List
from ncm.client import CryptoType, APIResponse, _create_options
from ncm.client import request
from ncm.infrastructure.http.decorators import ncm_api
import json


@ncm_api("/api/playlist/track/delete", ["GET","POST"])
async def playlist_track_delete(
        id: Union[str, int],
        ids: Union[str, List[Union[str, int]]],
        **kwargs
) -> APIResponse:
    """
    从歌单删除歌曲
    
    Args:
        id: 歌单ID
        ids: 要删除的歌曲ID，可以是单个ID、ID列表或逗号分隔的字符串
        **kwargs: 其他参数
        
    Returns:
        APIResponse: 包含删除结果的响应
    """
    # 处理歌曲ID参数
    if isinstance(ids, (list, tuple)):
        song_ids = [str(i) for i in ids]
    elif isinstance(ids, str):
        song_ids = ids.split(',') if ',' in ids else [ids]
    else:
        song_ids = [str(ids)]
    
    # 构建tracks参数
    tracks = [{"type": 3, "id": song_id} for song_id in song_ids]
    
    data = {
        'id': str(id),
        'tracks': json.dumps(tracks),
    }
    
    return await request("/api/playlist/track/delete", data, _create_options(CryptoType.WEAPI, **kwargs))