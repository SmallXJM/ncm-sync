from dataclasses import replace

from ncm.core.options import CryptoType, APIResponse, _create_options
from ncm.core.request import request
from ncm.infrastructure.utils import cookie_list_to_str
from ncm.infrastructure.http.decorators import ncm_api


@ncm_api("/api/login/status", ["GET", "POST"])
async def login_status(
        **kwargs
) -> APIResponse:
    data = {}
    return await request("/api/w/nuser/account/get", data, _create_options(CryptoType.WEAPI, **kwargs))


@ncm_api("/api/login/qr/key", ["GET","POST"])
async def login_qr_key(
        **kwargs
) -> APIResponse:
    data = {
        'type': 3
    }
    return await request("/api/login/qrcode/unikey", data, _create_options(**kwargs))


@ncm_api("/api/login/qr/check", ["GET","POST"])
async def login_qr_check(
        key: str,
        **kwargs
) -> APIResponse:
    """
    二维码登录状态检查接口 (轮询)。
    """
    data = {
        'key': key,
        'type': 3
    }
    resp = await request("/api/login/qrcode/client/login", data, _create_options(**kwargs))

    # 将 Cookie 数组注入到响应体中。
    cookie_str = cookie_list_to_str(resp.cookies)
    current_body = resp.body.copy()
    current_body['cookie'] = cookie_str

    return replace(
        resp,
        body=current_body
    )


@ncm_api("/api/login/qr/create", ["GET","POST"])
async def login_qr_create(
        key: str,
        qrimg: bool = True,
        platform: str = 'pc',
        **kwargs
) -> APIResponse:
    """
    根据 key 生成二维码的 URL 和 base64 图片。

    Args:
        key: 由 login_qr_key 接口获取的 codekey。
        qrimg: 是否同时生成 base64 格式的图片。
        platform: 平台类型 ('pc' 或 'web')。

    Returns:
        包含 qrurl 和 qrimg 的字典。
    """

    # 导入 qrcode 库 (需要确保环境中安装了 qrcode[pil])
    import qrcode

    # 1. 构建基础 URL
    url = f"https://music.163.com/login?codekey={key}"

    # 2. 如果是 web 平台，处理 chainId (您需要将 generateChainId 移植到 utils)
    if platform == 'web':
        # 假设您已将 generateChainId 移植到了 ncm/utils/auth.py
        from ...utils.tools import generate_chain_id

        # 从 Client 的 BaseClient 中获取当前 cookie 字符串
        cookie_str = kwargs.get("cookie")

        chainId = generate_chain_id(cookie_str)
        url += f"&chainId={chainId}"

    # 3. 生成图片
    qrimg_data = ""
    if qrimg:
        # ⚠️ 注意: qrcode 库通常是同步的，为了不阻塞 asyncio 循环，
        # 实际生产代码中应使用 run_in_executor 或确保使用的 qrcode 库是非阻塞的。

        # 为了简化，我们使用同步阻塞版本 (但需谨慎):
        qr_code_obj = qrcode.QRCode(version=1, border=2, box_size=3)
        qr_code_obj.add_data(url)
        qr_code_obj.make(fit=True)

        # 将 QR 码转换为 base64 字符串
        import io
        import base64
        img = qr_code_obj.make_image(fill_color="black", back_color="white")

        # 将 Image 对象保存到内存中的 PNG 文件
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")

        # 转换为 base64 字符串 (注意：Node.js 通常返回的是 data:image/png;base64,... 格式)
        base64_img = base64.b64encode(buffered.getvalue()).decode('utf-8')
        qrimg_data = f"data:image/png;base64,{base64_img}"

    mock_body = {
        "code": 200,
        "data": {
            "qrurl": url,
            "qrimg": qrimg_data,
        }
    }

    # 5. 返回 APIResponse 实例
    # 注意：这里我们使用 HTTP 状态码 200，并且 cookies/headers 为空字典/列表。
    return APIResponse(
        status=200,
        body=mock_body,
        cookies=[],
        headers={}
    )
