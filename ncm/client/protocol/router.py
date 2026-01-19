# api/router.py
from .options import CryptoType
from typing import Literal

DOMAIN = "https://music.163.com"
API_DOMAIN = "https://interface.music.163.com"


def build_url(uri: str, crypto: CryptoType) -> str:
    """
    Build full request URL depending on crypto type and incoming URI.
    Assumes `uri` is like "/api/xxx" (compatible with original project).
    """
    if crypto == CryptoType.WEAPI:
        # transform /api/xxx -> https://music.163.com/weapi/xxx (remove leading /api)
        if uri.startswith("/api"):
            return f"{DOMAIN}/weapi{uri[4:]}"
        return f"{DOMAIN}/weapi{uri}"

    if crypto == CryptoType.LINUXAPI:
        # linux forwarding endpoint
        return f"{DOMAIN}/api/linux/forward"

    if crypto == CryptoType.EAPI:
        if uri.startswith("/api"):
            return f"{API_DOMAIN}/eapi{uri[4:]}"
        return f"{API_DOMAIN}/eapi{uri}"

    # CryptoType.API or default
    return f"{API_DOMAIN}{uri}"
