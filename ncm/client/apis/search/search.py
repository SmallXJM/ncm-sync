# ncm/modules/search.py

from typing import Union
from ncm.client import APIResponse, _create_options
from ncm.client import request
from ncm.client.exceptions import ValidationError  # 假设这个异常仍然存在
from ncm.infrastructure.http.decorators import ncm_api

# --- Search Type Constants ---
SEARCH_TYPES = {
    "song": 1,  # 单曲
    "album": 10,  # 专辑
    "artist": 100,  # 歌手
    "playlist": 1000,  # 歌单
    "user": 1002,  # 用户
    "mv": 1004,  # MV
    "lyric": 1006,  # 歌词
    "radio": 1009,  # 电台
    "video": 1014,  # 视频
}


@ncm_api("/api/search", ["GET", "POST"])
async def search(
        keywords: str,
        type: Union[str, int] = "song",
        limit: int = 30,
        offset: int = 0,
        **kwargs
) -> APIResponse:
    """
    通用搜索 API。

    :param keywords: 搜索关键词。
    :param type: 搜索类型，可以是字符串 (如 "song") 或对应的整数 (如 1)。
    :param limit: 返回结果数量限制。
    :param offset: 列表偏移量，用于分页。
    :param kwargs: 可选参数，用于传递 options 或 cookie。
    :returns: APIResponse 包含搜索结果。
    """
    # 1. 参数校验和类型转换
    if not keywords.strip():
        raise ValidationError("搜索关键词不能为空")

    if isinstance(type, str):
        if type not in SEARCH_TYPES:
            raise ValidationError(f"无效的搜索类型: {type}")
        type_int = SEARCH_TYPES[type]
    else:
        type_int = type

    # 2. 构造请求数据 (Data)
    # 对应 Node.js 客户端中的 data 结构
    data = {
        # 关键词字段
        "s": keywords,
        # 搜索类型字段
        "type": type_int,
        "limit": limit,
        "offset": offset,
    }

    return await request(
        uri="/api/search/get",
        data=data,
        options=_create_options(**kwargs)
    )

