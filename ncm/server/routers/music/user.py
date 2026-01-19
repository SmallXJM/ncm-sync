"""User HTTP controller for music user functionality."""

import logging
import time
from typing import Union
from ncm.client import APIResponse
from ncm.api import ncm_service
from ncm.service.cookie.decorators import with_cookie
from ncm.client.apis import user

logger = logging.getLogger(__name__)


class UserController:
    """HTTP controller for music user functionality."""

    def __init__(self):
        """Initialize user controller."""
        self._cache = {}

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

        if uid is None or uid == "":  # 默认查找本cookie的歌单
            uid = session["account_id"]

        # Cache check for short-term deduplication (2 seconds)
        cache_key = f"{uid}_{limit}_{offset}_{include_video}"
        now = time.time()
        
        if cache_key in self._cache:
            ts, resp = self._cache[cache_key]
            if now - ts < 2.0:
                logger.info(f"Returning cached playlist for {uid}")
                return resp
            # Remove stale entry
            del self._cache[cache_key]

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

        # Cache success response
        # Simple cleanup if cache grows too large
        if len(self._cache) > 1000:
            self._cache.clear()
        self._cache[cache_key] = (now, resp_playlist)

        return resp_playlist
