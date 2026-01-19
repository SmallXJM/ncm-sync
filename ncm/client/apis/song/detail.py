from typing import Union, List
from ncm.client import CryptoType, APIResponse, _create_options
from ncm.client import request
from ncm.api import ncm_api


@ncm_api("/api/song/detail", ["GET", "POST"])
async def song_detail(
        ids: Union[int, str, List[int], List[str]],
        **kwargs
) -> APIResponse:
    """
    批量获取歌曲的详细信息。

    :param ids: 歌曲 ID，可以是逗号分隔的字符串或 ID 列表。
    :returns: APIResponse 包含歌曲详情的列表。
    """

    song_ids = []

    if isinstance(ids, str):
        # 对应 Node.js 逻辑: query.ids.split(/\s*,\s*/)
        # 使用正则表达式分割逗号，并去除空格 (但 Python 简单分割更常见且高效)
        song_ids = [s.strip() for s in ids.split(',') if s.strip()]

    elif isinstance(ids, int):
        # int 类型默认为单id
        song_ids = [str(ids)]

    else:
        # 如果是列表 (int 或 str)，转换为字符串列表
        for item in ids:
            if isinstance(item, dict):
                song_ids.append(str(item["id"]))
            else:
                song_ids.append(str(item))



    # 限制歌曲数量 (Node.js 代码建议不超过 1000，虽然没有强制截断逻辑，但我们保持兼容性)
    # song_ids = song_ids[:1000] # 如果需要限制数量，可以在这里添加截断逻辑

    # 2. 格式化为 '/api/v3/song/detail' 要求的 'c' 字段 JSON 字符串
    # 目标格式: '[{"id":123},{"id":456}]'

    # 使用列表推导式构造列表中的每一个 JSON 对象字符串
    ids_data_list = [f'{{"id":{id_str}}}' for id_str in song_ids]

    # 3. 构造最终的请求体 data
    data = {
        # 使用 f-string 构造最终的 JSON 数组字符串，作为 'c' 字段的值
        "c": f"[{','.join(ids_data_list)}]",
    }

    return await request(
        uri="/api/v3/song/detail",
        data=data,
        options=_create_options(CryptoType.WEAPI, **kwargs)
    )
