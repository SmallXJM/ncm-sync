import random
import ipaddress
from typing import List, Tuple, Union

# 中国 IP 段（来源：data/ChineseIPGenerate.csv）
CHINA_IP_RANGES_RAW: List[Tuple[str, str, int, str]] = [
    # 开始IP, 结束IP, IP个数, 位置
    ('1.0.1.0', '1.0.3.255', 768, '福州'),
    ('1.0.8.0', '1.0.15.255', 2048, '广州'),
    ('1.0.32.0', '1.0.63.255', 8192, '广州'),
    ('1.1.0.0', '1.1.0.255', 256, '福州'),
    ('1.1.2.0', '1.1.63.255', 15872, '广州'),
    ('1.2.0.0', '1.2.2.255', 768, '北京'),
    ('1.2.4.0', '1.2.127.255', 31744, '广州'),
    ('1.3.0.0', '1.3.255.255', 65536, '广州'),
    ('1.4.1.0', '1.4.127.255', 32512, '广州'),
    ('1.8.0.0', '1.8.255.255', 65536, '北京'),
    ('1.10.0.0', '1.10.9.255', 2560, '福州'),
    ('1.10.11.0', '1.10.127.255', 29952, '广州'),
    ('1.12.0.0', '1.15.255.255', 262144, '上海'),
    ('1.18.128.0', '1.18.128.255', 256, '北京'),
    ('1.24.0.0', '1.31.255.255', 524288, '赤峰'),
    ('1.45.0.0', '1.45.255.255', 65536, '北京'),
    ('1.48.0.0', '1.51.255.255', 262144, '济南'),
    ('1.56.0.0', '1.63.255.255', 524288, '伊春'),
    ('1.68.0.0', '1.71.255.255', 262144, '忻州'),
    ('1.80.0.0', '1.95.255.255', 1048576, '北京'),
    ('1.116.0.0', '1.117.255.255', 131072, '上海'),
    ('1.119.0.0', '1.119.255.255', 65536, '北京'),
    ('1.180.0.0', '1.185.255.255', 393216, '桂林'),
    ('1.188.0.0', '1.199.255.255', 786432, '洛阳'),
    ('1.202.0.0', '1.207.255.255', 393216, '铜仁'),
]


# Python 标准库的 ipaddress 模块提供了 ipToInt 和 intToIp 的等效功能
def ip_to_int(ip_str: str) -> int:
    """将 IP 字符串转换为整数。"""
    return int(ipaddress.IPv4Address(ip_str))


def int_to_ip(ip_int: int) -> str:
    """将整数转换为 IP 字符串。"""
    return str(ipaddress.IPv4Address(ip_int))


# 预计算 IP 段 (在模块加载时执行一次)
def build_ip_ranges(raw_ranges: List[Tuple[str, str, int, str]]) -> tuple[list[dict[str, Union[int, str]]], int]:
    """将原始 IP 范围转换为数值范围的列表，并计算总数。"""
    ranges = []
    total = 0
    for start_ip, end_ip, count_raw, location in raw_ranges:
        start_int = ip_to_int(start_ip)
        end_int = ip_to_int(end_ip)
        count = count_raw or end_int - start_int + 1

        ranges.append({
            'start': start_int,
            'end': end_int,
            'count': count,
            'location': location
        })
        total += count

    # 附带总数
    # ranges.total_count = total  # type: ignore
    return ranges, total


CHINA_IP_RANGES, CHINA_IP_TOTAL_COUNT = build_ip_ranges(CHINA_IP_RANGES_RAW)


def generate_ip_segment() -> int:
    """生成 IP 段（1 到 255）。"""
    return random.randint(1, 255)


def generate_random_chinese_ip() -> str:
    """
    从预定义的中国 IP 段中随机生成一个 IP。
    """
    total = CHINA_IP_TOTAL_COUNT  # type: ignore
    if not total:
        # 兜底逻辑
        ip = f"116.{random.randint(25, 94)}.{generate_ip_segment()}.{generate_ip_segment()}"
        # logger.info('Generated Random Chinese IP (fallback):', ip)
        return ip

    # 1. 选择一个全局随机偏移 ([0, total))
    offset = random.randint(0, total - 1)
    chosen = None

    # 2. 根据权重选择 IP 段
    for seg in CHINA_IP_RANGES:
        if offset < seg['count']:
            chosen = seg
            break
        offset -= seg['count']

    # 3. 如果没有选中（理论上不应该发生），回退到最后一个段
    if chosen is None:
        chosen = CHINA_IP_RANGES[-1]

    # 4. 在段内随机生成一个 IP
    seg_size = chosen['end'] - chosen['start'] + 1
    ip_int = chosen['start'] + random.randint(0, seg_size - 1)
    ip_str = int_to_ip(ip_int)

    # logger.info(
    #     'Generated Random Chinese IP:',
    #     ip_str,
    #     'location:',
    #     chosen['location'],
    # )
    return ip_str
