# api/request.py
from typing import Optional, Dict, Any, List
from urllib.parse import urlencode
import json

from .session import get_session
from .options import RequestOptions, APIResponse, CryptoType
from .cookies import process_cookie, cookie_dict_to_string
from .headers import build_headers, choose_user_agent, build_eapi_header
from .router import build_url
from .crypto import get_crypto_function, decrypt_eapi_response
from .exceptions import NetworkError, APIError, AuthenticationError, RateLimitError
from .logging import get_logger

logger = get_logger(__name__)

async def request(
    uri: str,
    data: Optional[Dict[str, Any]] = None,
    options: Optional[RequestOptions] = None
) -> APIResponse:
    method = "POST"

    """
    Unified HTTP request function — the only exported entry you need to call.
    Returns an APIResponse dataclass.
    """
    if options is None:
        options = RequestOptions()
    if data is None:
        data = {}

    client = await get_session(options)

    # process cookie and headers
    cookie_dict = process_cookie(options.cookie, uri, options)
    csrf_token = cookie_dict.get("__csrf", "")

    headers = build_headers(options, cookie_dict)

    if options.user_agent:
        headers["User-Agent"] = options.user_agent
    else:
        headers["User-Agent"] = choose_user_agent(options.crypto, options.os_type)

    # IP headers
    if options.real_ip:
        headers["X-Real-IP"] = options.real_ip
        headers["X-Forwarded-For"] = options.real_ip
    elif options.random_cn_ip:
        # simple fixed candidate IPs (can be improved)
        candidates = ["59.24.3.173", "218.205.77.4", "223.252.199.66", "27.19.222.18", "36.152.44.96"]
        headers["X-Real-IP"] = candidates[0]
        headers["X-Forwarded-For"] = candidates[0]

    url = build_url(uri, options.crypto)
    request_data = dict(data)  # shallow copy

    # per-crypto handling
    if options.crypto == CryptoType.WEAPI:
        headers["Referer"] = "https://music.163.com"
        request_data["csrf_token"] = csrf_token
        headers["Cookie"] = cookie_dict_to_string(cookie_dict)

    elif options.crypto == CryptoType.LINUXAPI:
        request_data = {
            "method": "POST",
            "url": f"https://music.163.com{uri}",
            "params": data
        }
        headers["Cookie"] = cookie_dict_to_string(cookie_dict)

    elif options.crypto in (CryptoType.API, CryptoType.EAPI):
        api_header = build_eapi_header(cookie_dict)
        headers["Cookie"] = cookie_dict_to_string(api_header)
        if options.crypto == CryptoType.EAPI:
            if api_header.get("MUSIC_U"):
                api_header.pop("MUSIC_U") # 真实客户端中 header 中没有 MUSIC_U
            request_data["header"] = json.dumps(api_header)
            request_data["e_r"] = options.encrypt_response

    # encryption
    crypto_func = get_crypto_function(options.crypto)
    if crypto_func and options.crypto != CryptoType.API:
        try:
            if options.crypto == CryptoType.EAPI:
                # some implementations expect (uri, data); our passthrough is simple
                encrypted = crypto_func(uri, request_data)
            else:
                encrypted = crypto_func(request_data)
        except TypeError:
            # support crypto functions that require different signature
            encrypted = crypto_func(request_data)
    else:
        encrypted = request_data

    # prepare body / url params
    body = None
    if options.crypto == CryptoType.API and method.upper() == "GET":
        if encrypted:
            url += "?" + urlencode(encrypted)
    else:
        # urlencode nested structures if needed; here we assume encrypted is dict of strings
        try:
            body = urlencode(encrypted)
        except Exception:
            # fallback: send json string if urlencode fails
            body = json.dumps(encrypted)

    try:
        logger.debug(f"\nrequest: {method} {url}\n{request_data}")
        resp = await client.request(
            method=method.upper(),
            url=url,
            headers=headers,
            content=body,
            timeout=options.timeout
        )

        # collect set-cookie simplified (httpx headers are case-insensitive mapping)
        response_cookies: List[str] = []
        cookie_map: dict[str, str] = {} # 只取最后一个cookie
        # raw_headers = resp.headers
        # httpx provides a cookies jar; but keep a simple approach
        for cookie in resp.cookies.jar:
            # name = cookie.name
            # value = cookie.value
            # service = cookie.service
            # path = cookie.path
            cookie_map[cookie.name] = cookie.value  # 后写覆盖前写
        response_cookies = [f"{k}={v}" for k, v in cookie_map.items()]
        # print(f"response_cookies: {response_cookies}")

        # parse body
        try:
            if options.crypto == CryptoType.EAPI and options.encrypt_response:
                body_data = decrypt_eapi_response(resp.content)
            else:
                body_data = resp.json()
        except Exception:
            body_data = {"message": resp.text}
            logger.exception(Exception)


        api_code = body_data.get("code", resp.status_code)
        if isinstance(api_code, str):
            try:
                api_code = int(api_code)
            except Exception:
                api_code = resp.status_code

        # Normalize some codes
        if api_code in (201, 302, 400, 502, 800, 801, 802, 803):
            status = 200
        else:
            status = api_code if 100 <= api_code < 600 else 400

        api_response = APIResponse(
            status=status,
            body=body_data,
            cookies=response_cookies,
            headers=dict(resp.headers)
        )

        # error handling
        if status != 200:
            if api_code == 301:
                raise AuthenticationError("需要登录", api_code, body_data)
            elif api_code == 503:
                raise RateLimitError("请求过于频繁", api_code, body_data)
            else:
                raise APIError(f"API请求失败: {body_data.get('message','未知错误')}", api_code, body_data)

        return api_response

    except (APIError, AuthenticationError, RateLimitError):
        raise
    except Exception as e:
        # network or unknown
        raise NetworkError(str(e))
