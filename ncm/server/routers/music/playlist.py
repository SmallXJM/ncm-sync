"""Playlist HTTP controller for music playlist functionality."""

import logging
from typing import Union
from ncm.client import APIResponse
from ncm.server.decorators import ncm_service
from ncm.service.cookie import with_cookie
from ncm.client.apis import playlist

logger = logging.getLogger(__name__)


class PlaylistController:
    """HTTP controller for music playlist functionality."""

    def __init__(self):
        """Initialize playlist controller."""
        pass

    @ncm_service("/ncm/music/playlist/detail", ["GET", "POST"])
    @with_cookie(max_retries=2)
    async def playlist_detail(self,
                              id: Union[str, None] = None,
                              **kwargs
                              ) -> APIResponse:
        # Get playlist basic info
        playlist_response = await playlist.detail(id=id, **kwargs)

        if not playlist_response.success:
            return APIResponse(
                status=playlist_response.status,
                body={
                    "code": playlist_response.code,
                    "message": f"获取歌单失败: {playlist_response.message}",
                    "error": playlist_response.body
                }
            )

        return playlist_response