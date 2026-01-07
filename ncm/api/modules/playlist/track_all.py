"""Playlist track all API - 获取歌单所有歌曲"""

from typing import Union
from ncm.core.options import APIResponse
from ncm.infrastructure.http.decorators import ncm_api
from .. import playlist

from .. import song


@ncm_api("/api/playlist/track/all", ["GET", "POST"])
async def playlist_track_all(
        id: Union[str, int],
        limit: int = 1000,
        offset: int = 0,
        s: int = 8,
        **kwargs
) -> APIResponse:
    """
    获取歌单所有歌曲详情

    通过歌单ID获取所有歌曲数据，支持分页

    Args:
        id: 歌单ID
        limit: 返回数量限制，默认1000
        offset: 偏移量，默认0
        s: 未知参数，默认8
        **kwargs: 其他参数

    Returns:
        APIResponse: 包含歌曲详情列表的响应
    """
    # 首先获取歌单详情，获取所有歌曲ID
    playlist_resp = await playlist.detail(id, s, **kwargs)

    if not playlist_resp.success or 'playlist' not in playlist_resp.body:
        return playlist_resp

    # 获取歌曲ID列表
    track_ids = playlist_resp.body['playlist'].get('trackIds', [])

    # 应用分页
    paginated_track_ids = track_ids[offset:offset + limit]

    # 获取歌曲详情
    return await song.detail(paginated_track_ids)

# async def playlist_track_all(
#         id: Union[str, int],
#         limit: int = 1000,
#         offset: int = 0,
#         s: int = 8,
#         **kwargs
# ) -> APIResponse:
#     """
#     获取歌单所有歌曲详情
#
#     通过歌单ID获取所有歌曲数据，支持分页
#
#     Args:
#         id: 歌单ID
#         limit: 返回数量限制，默认1000
#         offset: 偏移量，默认0
#         s: 未知参数，默认8
#         **kwargs: 其他参数
#
#     Returns:
#         APIResponse: 包含歌曲详情列表的响应
#     """
#     # 首先获取歌单详情，获取所有歌曲ID
#     playlist_data = {
#         'id': str(id),
#         'n': 100000,
#         's': s,
#     }
#
#     playlist_resp = await request("/api/v6/playlist/detail", playlist_data, _create_options(CryptoType.WEAPI, **kwargs))
#
#     if not playlist_resp.success or 'playlist' not in playlist_resp.body:
#         return playlist_resp
#
#     # 获取歌曲ID列表
#     track_ids = playlist_resp.body['playlist'].get('trackIds', [])
#
#     if not track_ids:
#         # 如果没有歌曲，返回空列表
#         return APIResponse(
#             status=200,
#             body={
#                 'code': 200,
#                 'songs': [],
#                 'privileges': []
#             },
#             headers=playlist_resp.headers,
#             cookies=playlist_resp.cookies
#         )
#
#     # 应用分页
#     paginated_track_ids = track_ids[offset:offset + limit]
#
#     # 构建歌曲详情请求参数
#     song_ids = [{'id': track['id']} for track in paginated_track_ids]
#     songs_data = {
#         'c': str(song_ids).replace("'", '"')  # 转换为JSON格式字符串
#     }
#
#     # 获取歌曲详情
#     return await request("/api/v3/song/detail", songs_data, _create_options(CryptoType.WEAPI, **kwargs))
