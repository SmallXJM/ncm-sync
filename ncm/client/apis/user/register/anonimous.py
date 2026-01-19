# ncm/modules/anonimous.py

import base64
import hashlib
from dataclasses import replace
from ncm.client import CryptoType, APIResponse, _create_options
from ncm.client import request
from ncm.infrastructure.utils import generate_device_id, cookie_list_to_str
from ncm.infrastructure.http.decorators import ncm_api
from ncm.core.logging import get_logger

logger = get_logger(__name__)



ID_XOR_KEY_1 = '3go8&$8*3*3h0k(2)2'


def cloudmusic_dll_encode_id(some_id: str) -> str:
    """
    实现 Node.js 中的 cloudmusic_dll_encode_id 逻辑。
    步骤: 异或 (XOR) -> MD5 Hash -> Base64 编码。

    :param some_id: 设备 ID (deviceId)
    :return: Base64 编码的 MD5 摘要。
    """
    xored_bytes = []
    key_len = len(ID_XOR_KEY_1)

    # 1. 异或 (XOR) 操作
    for i in range(len(some_id)):
        # some_id.charCodeAt(i) ^ ID_XOR_KEY_1.charCodeAt(i % ID_XOR_KEY_1.length)
        char_code = (
                ord(some_id[i]) ^ ord(ID_XOR_KEY_1[i % key_len])
        )
        xored_bytes.append(char_code)

    # 将字符编码转换后的整数列表转换为字节串 (假设原 JS 输出是 UTF-8 兼容的)
    xored_string = bytes(xored_bytes)

    # 2. MD5 Hash (对应 CryptoJS.MD5(wordArray))
    digest = hashlib.md5(xored_string).digest()

    # 3. Base64 编码 (对应 CryptoJS.enc.Base64.stringify(digest))
    return base64.b64encode(digest).decode('utf-8')


# 匿名注册 API
@ncm_api("/api/register/anonimous", ["GET","POST"])
async def register_anonimous(
        **kwargs
) -> APIResponse:
    """
    匿名用户注册，用于获取匿名登录 Cookie (可用于部分接口)。

    :returns: APIResponse 包含匿名登录后的 cookie。
    """
    # 1. 生成 deviceId (与 JS 的 generateDeviceId 对应)
    device_id = generate_device_id()
    logger.debug(f"device_id: {device_id}")

    # 2. DLL 编码 ID
    encoded_dll_id = cloudmusic_dll_encode_id(device_id)

    # 3. 构建最终的 username 字符串 (对应 `${deviceId} ${cloudmusic_dll_encode_id(deviceId)}`)
    username_str = f"{device_id} {encoded_dll_id}"

    # 4. Base64 编码 username (对应 CryptoJS.enc.Base64.stringify(CryptoJS.enc.Utf8.parse(...)))
    encoded_username = base64.b64encode(username_str.encode('utf-8')).decode('utf-8')

    # 5. 构造最终的 data
    data = {
        'username': encoded_username,
    }

    resp = await request("/api/register/anonimous", data, _create_options(CryptoType.WEAPI, **kwargs))

    # 仅在 code 200 时进行处理 (与 JS 逻辑 if (result.body.code === 200) 对齐)
    if resp.code == 200:
        cookie_str = cookie_list_to_str(resp.cookies)
        current_body = resp.body.copy()
        current_body['cookie'] = cookie_str

        return replace(
            resp,
            body=current_body
        )
    return resp
