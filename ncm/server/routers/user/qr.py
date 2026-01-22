"""Authentication HTTP controller - unified auth functionality."""

from typing import Dict, Any, Optional

from ncm.service.cookie import get_cookie_manager, with_cookie
from ncm.client.apis.user import login
from ncm.client import APIResponse
from ncm.core.logging import get_logger
from ncm.server.decorators import ncm_service

logger = get_logger(__name__)


class QRAuthController:
    """HTTP controller for authentication functionality."""

    def __init__(self):
        """Initialize auth controller."""
        self.cookie_manager = get_cookie_manager()

    # ==================== QR Login ====================
    @ncm_service("/ncm/user/qr/start", ["POST"])
    async def start_qr_login(self, **kwargs) -> APIResponse:
        """Start QR code login workflow."""
        try:
            # Step 1: Get QR key
            key_response = await login.qr_key(**kwargs)
            if not key_response.success:
                return APIResponse(
                    status=key_response.status,
                    body={
                        "code": key_response.code,
                        "message": "Failed to get QR key",
                        "error": key_response.body
                    }
                )
            
            qr_key = key_response.body.get("unikey")
            if not qr_key:
                return APIResponse(
                    status=400,
                    body={
                        "code": 400,
                        "message": "No QR key in response",
                        "error": key_response.body
                    }
                )
            
            # Step 2: Generate QR code
            qr_response = await login.qr_create(qr_key, **kwargs)
            if not qr_response.success:
                return APIResponse(
                    status=qr_response.status,
                    body={
                        "code": qr_response.code,
                        "message": "Failed to create QR code",
                        "error": qr_response.body
                    }
                )
            
            return APIResponse(
                status=200,
                body={
                    "code": 200,
                    "message": "QR login started successfully",
                    "data": {
                        "qr_key": qr_key,
                        "qr_url": qr_response.body["data"]["qrurl"],
                        "qr_img": qr_response.body["data"]["qrimg"],
                        "status": "waiting_scan"
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"QR login start failed: {str(e)}")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"QR login start failed: {str(e)}"
                }
            )
    
    @ncm_service("/ncm/user/qr/check", ["POST"])
    async def check_qr_login(self, qr_key: str, **kwargs) -> APIResponse:
        """Check QR code login status."""
        try:
            response = await login.qr_check(qr_key, **kwargs)
            
            # Handle different status codes
            code = response.body.get("code", response.status)
            
            if code == 803:
                # Login successful
                cookie = response.body.get("cookie")
                if cookie:
                    # Save user info to database
                    await self.cookie_manager.add_session(cookie, "qr")
                
                return APIResponse(
                    status=200,
                    body={
                        "code": 200,
                        "message": "登录成功",
                        "data": {
                            "status": "success",
                            "cookie": cookie
                        }
                    }
                )

            elif code == 800:
                return APIResponse(
                    status=200,
                    body={
                        "code": 803,
                        "message": "二维码已过期",
                        "data": {"status": "expired"}
                    }
                )
            
            elif code == 801:
                return APIResponse(
                    status=200,
                    body={
                        "code": 801,
                        "message": "等待扫码",
                        "data": {"status": "waiting_scan"}
                    }
                )
            
            elif code == 802:
                return APIResponse(
                    status=200,
                    body={
                        "code": 802,
                        "message": "待确认",
                        "data": {"status": "waiting_confirm"}
                    }
                )
            
            else:
                return APIResponse(
                    status=200,
                    body={
                        "code": code,
                        "message": response.body.get("message", "未知错误"),
                        "data": {"status": "error"}
                    }
                )
                
        except Exception as e:
            logger.error(f"QR login check failed: {str(e)}")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"QR login check failed: {str(e)}"
                }
            )


