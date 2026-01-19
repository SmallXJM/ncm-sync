import urllib.parse
from typing import List, Tuple, Dict, Any, Optional, Union


def cookie_to_json(cookie_str: Optional[str]) -> Dict[str, str]:
    """
    将 HTTP Cookie 字符串转换为字典。
    """
    if not cookie_str:
        return {}

    obj = {}
    # 使用 for 循环优化性能
    for item in cookie_str.split(';'):
        item = item.strip()
        if not item:
            continue

        # 使用 find/split 优化性能
        eq_index = item.find('=')
        if eq_index > 0:
            key = item[:eq_index].strip()
            value = item[eq_index + 1:].strip()
            # Node.js 中的 trim()
            obj[key] = value

    return obj


def cookie_obj_to_string(cookie_obj: Dict[str, str]) -> str:
    """
    将 Cookie 字典转换为 HTTP Cookie 字符串。
    """
    result = []
    # 使用 urllib.parse.quote_plus (等同于 encodeURIComponent)
    for key, value in cookie_obj.items():
        result.append(f"{urllib.parse.quote(key)}={urllib.parse.quote(value)}")

    return "; ".join(result)


def get_cookie_value(cookie_str: Optional[str], key: str) -> Optional[str]:
    """
    从 Cookie 字符串中提取指定 key 的值。
    """
    if not cookie_str:
        return None

    # 转换为字典后查找是最健壮和易读的方式
    cookie_dict = cookie_to_json(cookie_str)
    return cookie_dict.get(key)

def cookie_list_to_str(cookie: List[str]) -> str:
    return "; ".join(cookie)
