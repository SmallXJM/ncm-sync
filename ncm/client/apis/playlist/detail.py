from ncm.client import CryptoType, APIResponse, _create_options
from ncm.client import request
from ncm.infrastructure.http.decorators import ncm_api

@ncm_api("/api/playlist/detail", ["GET", "POST"])
async def playlist_detail(
        id: int,
        s: int = 8,
        **kwargs
) -> APIResponse:
    data = {
        'id': id,
        'n': 100000,
        's': s,
    }
    return await request("/api/v6/playlist/detail", data, _create_options(CryptoType.WEAPI, **kwargs))