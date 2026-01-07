"""User HTTP controller for music user functionality."""

import logging
from typing import List, Dict, Any, Union
from ncm.core.options import APIResponse
from ncm.infrastructure.http import ncm_service
from ncm.service.cookie.decorators import with_cookie
from ncm.api.modules import user

logger = logging.getLogger(__name__)


class UserController:
    """HTTP controller for music user functionality."""

    def __init__(self):
        """Initialize user controller."""
        pass

    @ncm_service("/ncm/music/user/playlist", ["GET", "POST"])
    @with_cookie(max_retries=2)
    async def user_playlist(self,
                            uid: Union[str, int, None] = None,
                            limit: int = 30,
                            offset: int = 0,
                            include_video: bool = True,
                            **kwargs
                            ) -> APIResponse:
        session = kwargs["_session"]

        if uid is None:  # 默认查找本cookie的歌单
            uid = session["account_id"]

        # Get playlist basic info
        resp_playlist = await user.playlist(uid, limit, offset, include_video, **kwargs)

        if not resp_playlist.success:
            return APIResponse(
                status=resp_playlist.status,
                body={
                    "code": resp_playlist.code,
                    "message": f"获取用户歌单列表失败: {resp_playlist.message}",
                    "error": resp_playlist.body
                }
            )

        return resp_playlist
