from ncm.client import APIResponse, _create_options
from ncm.client import request
from ncm.api import ncm_api


@ncm_api("/api/search/hot", ["GET", "POST"])
async def search_hot(
        **kwargs
) -> APIResponse:
    data = {
        'type': 1111,
    }
    return await request("/api/search/hot", data, _create_options(**kwargs))
