# api/session.py
import asyncio
import httpx
from typing import Optional

from ncm.client import RequestOptions
from ncm.core.logging import get_logger

logger = get_logger(__name__)

_session: Optional[httpx.AsyncClient] = None
_session_proxy: Optional[str] = None
_lock = asyncio.Lock()


async def _create_session(options: RequestOptions) -> httpx.AsyncClient:
    logger.debug(
        "Create new AsyncClient (proxy=%s)",
        options.proxy
    )
    return httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
        http2=True,
        proxy=options.proxy,
        verify=False if options.proxy else True,
    )


async def get_session(
    options: Optional[RequestOptions] = None
) -> httpx.AsyncClient:
    """
    Get or create a shared AsyncClient instance.
    Recreate session when proxy changes.
    """
    global _session, _session_proxy

    if options is None:
        raise ValueError("RequestOptions is required")

    async with _lock:
        need_recreate = (
            _session is None
            or _session.is_closed
            or _session_proxy != options.proxy
        )

        if need_recreate:
            if _session is not None and not _session.is_closed:
                logger.debug(
                    "Proxy changed (%s -> %s), closing old session",
                    _session_proxy,
                    options.proxy,
                )
                await _session.aclose()

            _session = await _create_session(options)
            _session_proxy = options.proxy

        return _session


async def close_session() -> None:
    """
    Close shared session (optional cleanup).
    """
    global _session, _session_proxy

    async with _lock:
        if _session is not None and not _session.is_closed:
            await _session.aclose()
        _session = None
        _session_proxy = None
