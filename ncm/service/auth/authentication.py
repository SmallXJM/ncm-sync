"""Authentication business logic orchestration."""

import asyncio
from typing import Dict, Any, List
from ncm.infrastructure.db import AccountRepository
from ncm.api.modules.user import login
from ncm.core.logging import get_logger
from ncm.service.cookie import get_cookie_manager

logger = get_logger(__name__)


async def upload_and_validate_cookie(cookie: str, login_status_service, **kwargs) -> Dict[str, Any]:
    """
    Upload and validate cookie business logic.

    Args:
        cookie: Cookie string to upload and validate
        login_status_service: Service to validate cookie

    Returns:
        Dict containing validation result and user info
    """
    try:
        # Validate cookie by getting user info
        user_info = await login_status_service.get_user_info_from_cookie(cookie, **kwargs)

        if not user_info:
            return {
                "success": False,
                "code": 400,
                "message": "Cookie 无效或已过期"
            }

        # Save user login with cookie
        result = await login_status_service.save_user_login(user_info, cookie, "cookie_upload")

        return {
            "success": True,
            "code": 200,
            "message": "Cookie 上传成功",
            "data": {
                "user_info": user_info,
                "account": result.get("account"),
                "session": result.get("session")
            }
        }

    except Exception as e:
        logger.exception(f"Cookie 上传失败")
        return {
            "success": False,
            "code": 500,
            "message": f"Cookie 上传失败: {str(e)}"
        }


async def validate_cookie_only(cookie: str, login_status_service, **kwargs) -> Dict[str, Any]:
    """
    Validate cookie without saving to database.

    Args:
        cookie: Cookie string to validate
        login_status_service: Service to validate cookie

    Returns:
        Dict containing validation result
    """
    try:
        # Validate cookie by getting user info
        user_info = await login_status_service.get_user_info_from_cookie(cookie, **kwargs)

        if not user_info:
            return {
                "success": True,
                "code": 400,
                "message": "Cookie 无效或已过期",
                "data": {"valid": False}
            }

        return {
            "success": True,
            "code": 200,
            "message": "Cookie 有效",
            "data": {
                "valid": True,
                "user_info": user_info
            }
        }

    except Exception as e:
        logger.error(f"Cookie 验证失败: {str(e)}")
        return {
            "success": False,
            "code": 500,
            "message": f"Cookie 验证失败: {str(e)}",
            "data": {"valid": False}
        }




async def check_qr_login_status(qr_key: str, **kwargs) -> Dict[str, Any]:
    """
    Check QR login status and handle cookie extraction.

    Args:
        qr_key: QR code key

    Returns:
        Dict containing login status and user info
    """
    try:
        # Call the login check API
        response = await login.qr_check(qr_key, **kwargs)

        if not response.success:
            return {
                "success": False,
                "code": response.status,
                "message": "QR 登录检查失败"
            }

        code = response.body.get("code", -1)
        message = response.body.get("message", "")

        # Handle different status codes
        if code == 803:  # Login successful
            # Extract cookie from response
            cookie = response.body.get("cookie", "")
            if not cookie:
                return {
                    "success": False,
                    "code": 500,
                    "message": "登录成功但未获取到 Cookie"
                }

            # Get user info and save login
            # This would typically call login_status_service
            # For now, return success with cookie
            return {
                "success": True,
                "code": 200,
                "message": "QR 登录成功",
                "data": {
                    "status": "success",
                    "cookie": cookie
                }
            }

        elif code == 800:  # QR code expired
            return {
                "success": True,
                "code": 200,
                "message": "二维码已过期",
                "data": {"status": "expired"}
            }

        elif code == 801:  # Waiting for scan
            return {
                "success": True,
                "code": 200,
                "message": "等待扫码",
                "data": {"status": "waiting_scan"}
            }

        elif code == 802:  # Waiting for confirmation
            return {
                "success": True,
                "code": 200,
                "message": "待确认",
                "data": {"status": "waiting_confirm"}
            }

        else:
            return {
                "success": False,
                "code": code,
                "message": message or "未知状态"
            }

    except Exception as e:
        logger.error(f"QR 登录状态检查失败: {str(e)}")
        return {
            "success": False,
            "code": 500,
            "message": f"QR 登录状态检查失败: {str(e)}"
        }


async def complete_qr_login_workflow(qr_key: str, timeout: int = 300, **kwargs) -> Dict[str, Any]:
    """
    Complete QR login workflow with polling.

    Args:
        qr_key: QR code key
        timeout: Timeout in seconds

    Returns:
        Dict containing workflow result
    """
    start_time = asyncio.get_event_loop().time()

    while True:
        current_time = asyncio.get_event_loop().time()
        if current_time - start_time > timeout:
            return {
                "success": False,
                "code": 408,
                "message": "QR login timeout"
            }

        try:
            # Check QR login status
            result = await check_qr_login_status(qr_key, **kwargs)

            # Check if workflow is complete
            status = result.get("data", {}).get("status")
            if status in ["success", "expired", "error"]:
                return result

            # Wait before next check
            await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"QR login workflow failed: {str(e)}")
            return {
                "success": False,
                "code": 500,
                "message": f"QR login workflow failed: {str(e)}"
            }


class AuthenticationService:
    """Business logic for authentication workflows."""

    def __init__(self):
        """Initialize authentication service."""
        self.account_repo = AccountRepository()
        self.cookie_manager = get_cookie_manager()

    def list_available_cookies(self) -> Dict[str, Any]:
        """
        List all available cookies with their account information.
        
        Returns:
            Dict containing list of available cookies and accounts
        """
        try:
            # Get all sessions from cookie manager
            sessions = self.cookie_manager.list_all_sessions()

            # Filter only valid sessions
            valid_sessions = [s for s in sessions if s.is_valid]

            cookie_list = []
            for session in valid_sessions:
                cookie_info = {
                    "session_id": session.session_id,
                    "account_id": session.account_id,
                    "nickname": session.nickname,
                    "avatar_url": session.avatar_url,
                    "login_type": session.login_type,
                    "last_success_at": session.last_success_at,
                    "is_current": session.is_current,
                    "created_at": session.created_at
                }
                cookie_list.append(cookie_info)

            return {
                "success": True,
                "code": 200,
                "message": f"找到 {len(cookie_list)} 个有效 Cookie",
                "data": {
                    "total_cookies": len(cookie_list),
                    "current_cookie": self.cookie_manager.get_current_session_id(),
                    "cookies": cookie_list
                }
            }

        except Exception as e:
            logger.error(f"获取 Cookie 列表失败: {str(e)}")
            return {
                "success": False,
                "code": 500,
                "message": f"获取 Cookie 列表失败: {str(e)}"
            }

