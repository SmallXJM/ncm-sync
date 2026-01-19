# ncm/utils/device.py

import random
import time
from typing import List, Tuple, Dict, Any, Optional, Union

from ncm.core.cookie import get_cookie_value


def get_random(num: int) -> int:
    """
    生成特定位数的随机数 (复制原 Node.js 复杂逻辑)。
    """
    # 警告：原 JS 逻辑 (var randomNum = floor((randomValue + floorValue) * powValue))
    # 实际上是为了生成一个 N 位数。Python 中我们使用更简单的方法模拟其效果。

    # Node.js: var floorValue = floor(randomValue * 9 + 1) -> 确保 floorValue >= 1

    random_value = random.random()
    floor_value = random.randint(1, 9)
    pow_value = 10 ** (num - 1)

    # 由于 Python 的随机数精度和 JS 不同，这里直接生成指定位数的整数。
    # 模拟原意：生成一个大于等于 10^(num-1) 的 num 位整数

    # 简单实现：
    min_val = 10 ** (num - 1)
    max_val = 10 ** num - 1
    return random.randint(min_val, max_val)




def generate_chain_id(cookie_string: Optional[str]) -> str:
    """
    生成用于二维码登录的 chainId (Node.js 移植)。
    """
    version = 'v1'
    random_num = random.randint(0, 999999)

    # 提取 sDeviceId
    device_id = get_cookie_value(cookie_string, 'sDeviceId')

    # 如果不存在，使用 'unknown-' + randomNum
    if not device_id:
        device_id = f'unknown-{random_num}'

    platform = 'web'
    action = 'login'
    # Node.js: Date.now() 返回毫秒时间戳
    timestamp = int(time.time() * 1000)

    return f"{version}_{device_id}_{platform}_{action}_{timestamp}"


def generate_device_id() -> str:
    """
    生成一个 52 位的随机十六进制字符串作为 deviceId。
    """
    hex_chars = '0123456789ABCDEF'

    # 使用 random.choices 效率更高
    chars = random.choices(hex_chars, k=52)
    return "".join(chars)


