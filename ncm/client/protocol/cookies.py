# api/cookies.py
import random
import time
from typing import Dict, Any, Optional, Union

from .options import RequestOptions, OSType


def _gen_hex(n: int) -> str:
    import secrets
    return secrets.token_hex(n // 2) if n % 2 == 0 else secrets.token_hex((n + 1) // 2)


def _default_os_config():
    return {
        OSType.PC: {"os": "pc", "appver": "3.1.17.204416", "osver": "Microsoft-Windows-10"},
        OSType.LINUX: {"os": "linux", "appver": "1.2.1", "osver": "Linux"},
        OSType.ANDROID: {"os": "android", "appver": "8.20.20", "osver": "14"},
        OSType.IPHONE: {"os": "iPhone OS", "appver": "9.0.90", "osver": "16.2"},
    }


def process_cookie(cookie: Optional[Union[str, Dict[str, str]]], uri: str, options: RequestOptions) -> Dict[str, str]:
    """
    Normalise cookie into dict and inject defaults expected by Netease API calls.
    """
    if isinstance(cookie, str):
        cookie_dict: Dict[str, str] = {}
        for item in cookie.split(";"):
            if "=" in item:
                k, v = item.strip().split("=", 1)
                cookie_dict[k] = v
    elif isinstance(cookie, dict):
        cookie_dict = dict(cookie)
    else:
        cookie_dict = {}

    os_cfg_map = _default_os_config()
    os_cfg = os_cfg_map.get(options.os_type, os_cfg_map[OSType.PC]) if hasattr(options, "os_type") else os_cfg_map[OSType.PC]

    ntes_nuid = _gen_hex(32)
    timestamp = str(int(time.time() * 1000))

    processed = {
        "__remember_me": "true",
        "ntes_kaola_ad": "1",
        "_ntes_nuid": cookie_dict.get("_ntes_nuid", ntes_nuid),
        "_ntes_nnid": cookie_dict.get("_ntes_nnid", f"{ntes_nuid},{timestamp}"),
        "WEVNSM": cookie_dict.get("WEVNSM", "1.0.0"),
        "osver": cookie_dict.get("osver", os_cfg["osver"]),
        "deviceId": cookie_dict.get("deviceId", options.device_id or _gen_hex(32)),
        "os": cookie_dict.get("os", os_cfg["os"]),
        "channel": cookie_dict.get("channel", cookie_dict.get("channel", "netease")),
        "appver": cookie_dict.get("appver", os_cfg["appver"]),
        **cookie_dict,
    }

    # add NMTID for non-login
    if "login" not in uri:
        processed.setdefault("NMTID", _gen_hex(16))

    if not cookie_dict.get("MUSIC_U"):
        # add anonymous token placeholder if MUSIC_U missing (client may override)
        processed.setdefault("MUSIC_A", cookie_dict.get("MUSIC_A", ""))

    return processed


def cookie_dict_to_string(cookie_dict: Dict[str, str]) -> str:
    return "; ".join(f"{k}={v}" for k, v in cookie_dict.items())
