# api/headers.py
from typing import Dict
from .options import CryptoType, OSType


_USER_AGENTS = {
    CryptoType.WEAPI: {
        OSType.PC: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"
    },
    CryptoType.LINUXAPI: {
        OSType.LINUX: "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/60.0.3112.90 Safari/537.36"
    },
    CryptoType.API: {
        OSType.PC: "NeteaseMusicDesktop/3.0.18.203152",
        OSType.ANDROID: "NeteaseMusic/9.1.65 Dalvik/2.1.0",
        OSType.IPHONE: "NeteaseMusic 9.0.90/5038 (iPhone; iOS 16.2)"
    }
}
# EAPI uses same UA as API
_USER_AGENTS[CryptoType.EAPI] = _USER_AGENTS[CryptoType.API]


def choose_user_agent(crypto: CryptoType, os_type: OSType) -> str:
    return _USER_AGENTS.get(crypto, {}).get(os_type, list(_USER_AGENTS.get(crypto, {}).values())[0] if _USER_AGENTS.get(crypto) else "")


def build_headers(options, cookie_dict=None) -> Dict[str, str]:
    """
    Build common headers. Caller may set/override User-Agent, Cookie, Referer, etc.
    """
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        **(options.headers or {})
    }
    return headers


def build_eapi_header(cookie_dict: Dict[str, str]) -> Dict[str, str]:
    """
    Build header-like cookie map used by API/EAPI flows.
    """
    header = {
        "osver": cookie_dict.get("osver", ""),
        "deviceId": cookie_dict.get("deviceId", ""),
        "os": cookie_dict.get("os", ""),
        "appver": cookie_dict.get("appver", ""),
        "versioncode": "140",
        "mobilename": "",
        "buildver": str(int(__import__("time").time())),
        "resolution": "1920x1080",
        "__csrf": cookie_dict.get("__csrf", ""),
        "channel": cookie_dict.get("channel", "netease"),
        "requestId": f"{int(__import__('time').time() * 1000)}_{__import__('random').randint(0,9999):04d}"
    }
    if cookie_dict.get("MUSIC_U"):
        header["MUSIC_U"] = cookie_dict["MUSIC_U"]
    if cookie_dict.get("MUSIC_A"):
        header["MUSIC_A"] = cookie_dict["MUSIC_A"]
    return header
