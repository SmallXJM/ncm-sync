"""Song URL API - 歌曲播放链接"""

from typing import Union, List
from ncm.client import CryptoType, APIResponse, _create_options
from ncm.client import request
from ncm.infrastructure.http.decorators import ncm_api
import json


@ncm_api("/api/song/url", ["GET", "POST"])
async def song_url(
        id: Union[str, int, List[Union[str, int]]],
        br: int = 999000,
        **kwargs
) -> APIResponse:
    """
    获取歌曲播放链接
    
    Args:
        id: 歌曲ID，可以是单个ID或ID列表（逗号分隔的字符串）
        br: 音质，默认999000（无损）
        **kwargs: 其他参数
        
    Returns:
        APIResponse: 包含歌曲播放链接的响应
    """
    # 处理ID参数
    if isinstance(id, (list, tuple)):
        ids = [str(i) for i in id]
    elif isinstance(id, str) and ',' in id:
        ids = id.split(',')
    else:
        ids = [str(id)]
    
    data = {
        'ids': json.dumps(ids),
        'br': int(br),
    }
    
    resp = await request("/api/song/enhance/player/url", data, _create_options(CryptoType.WEAPI, **kwargs))
    
    if not resp.success:
        return resp
    
    # 根据传入的ID顺序排序结果
    result_data = resp.body.get('data', [])
    if result_data and len(ids) > 1:
        # 创建ID到索引的映射
        id_order = {str(song_id): idx for idx, song_id in enumerate(ids)}
        
        # 按照原始ID顺序排序
        result_data.sort(key=lambda x: id_order.get(str(x.get('id', '')), float('inf')))
    
    # 返回标准化的响应格式
    return APIResponse(
        status=200,
        body={
            'code': 200,
            'data': result_data,
        },
        headers=resp.headers,
        cookies=resp.cookies
    )