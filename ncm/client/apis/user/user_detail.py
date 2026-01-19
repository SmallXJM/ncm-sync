"""User detail API - 用户详情"""

from typing import Union
from ncm.client import CryptoType, APIResponse, _create_options
from ncm.client import request
from ncm.client.decorators import ncm_api
import json


@ncm_api("/api/user/detail", ["GET", "POST"])
async def user_detail(
        uid: Union[str, int],
        **kwargs
) -> APIResponse:
    """
    获取用户详情
    
    Args:
        uid: 用户ID
        **kwargs: 其他参数
        
    Returns:
        APIResponse: 包含用户详情的响应
    """
    resp = await request(f"/api/v1/user/detail/{uid}", {}, _create_options(CryptoType.WEAPI, **kwargs))
    
    if not resp.success:
        return resp
    
    # 处理字段名称，将 avatarImgId_str 替换为 avatarImgIdStr
    try:
        body_str = json.dumps(resp.body)
        body_str = body_str.replace('avatarImgId_str', 'avatarImgIdStr')
        processed_body = json.loads(body_str)
        
        return APIResponse(
            status=resp.status,
            body=processed_body,
            headers=resp.headers,
            cookies=resp.cookies
        )
    except (json.JSONDecodeError, TypeError):
        # 如果处理失败，返回原始响应
        return resp