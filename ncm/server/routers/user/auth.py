"""Authentication HTTP controller - unified auth functionality."""

from typing import Dict, Any, Optional

from ncm.service.auth import AuthenticationService
from ncm.service.cookie import get_cookie_manager, with_cookie
from ncm.infrastructure.db import AccountRepository
from ncm.infrastructure.db.session import get_session
from ncm.client.apis.user import login
from ncm.client import APIResponse
from ncm.core.logging import get_logger
from ncm.api import ncm_service

logger = get_logger(__name__)


class AuthController:
    """HTTP controller for authentication functionality."""

    def __init__(self):
        """Initialize auth controller."""
        self.account_repo = AccountRepository()
        self.cookie_manager = get_cookie_manager()
        self.auth_service = AuthenticationService()

    # ==================== Cookie Management ====================
    
    @ncm_service("/ncm/user/cookie/upload", ["POST"])
    async def upload_cookie(self, cookie: str, **kwargs) -> APIResponse:
        """Upload and validate cookie directly."""
        try:
            result = await self.upload_and_validate_cookie(
                cookie, **kwargs
            )
            
            return APIResponse(
                status=200 if result["success"] else 400,
                body={
                    "code": result["code"],
                    "message": result["message"],
                    "data": result.get("data")
                }
            )

        except Exception as e:
            logger.exception(f"Cookie 上传失败")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"Cookie 上传失败: {str(e)}"
                }
            )

    @ncm_service("/ncm/user/cookie/validate", ["POST"])
    async def validate_cookie(self, cookie: str, **kwargs) -> APIResponse:
        """Validate cookie without saving to database."""
        try:
            result = await self.validate_cookie_only(
                cookie, **kwargs
            )
            
            return APIResponse(
                status=200,
                body={
                    "code": result["code"],
                    "message": result["message"],
                    "data": result.get("data")
                }
            )

        except Exception as e:
            logger.error(f"Cookie 验证失败: {str(e)}")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"Cookie 验证失败: {str(e)}",
                    "data": {"valid": False}
                }
            )



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
                    user_info = await self.get_user_info_from_cookie(cookie, **kwargs)
                    if user_info:
                        await self.save_user_login(user_info, cookie, "qr")
                
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

    # ==================== Login Status ====================
    
    @ncm_service("/ncm/user/status", ["GET", "POST"])
    @with_cookie
    async def get_login_status(self, **kwargs) -> APIResponse:
        """Get current login status using available cookie."""
        try:
            response = await login.status(**kwargs)

            if response.success and response.body.get("account"):
                # User is logged in
                account = response.body["account"]
                profile = response.body.get("profile", {})

                return APIResponse(
                    status=200,
                    body={
                        "code": 200,
                        "message": "获取登录状态成功",
                        "data": {
                            "logged_in": True,
                            "user_id": str(account.get("id", "")),
                            "nickname": profile.get("nickname", ""),
                            "avatar_url": profile.get("avatarUrl", ""),
                            "account": account,
                            "profile": profile
                        }
                    }
                )
            else:
                return APIResponse(
                    status=200,
                    body={
                        "code": 401,
                        "message": "未登录",
                        "data": {"logged_in": False}
                    }
                )

        except Exception as e:
            logger.error(f"获取登录状态失败: {str(e)}")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"获取登录状态失败: {str(e)}",
                    "data": {"logged_in": False}
                }
            )

    def get_local_login_status(self) -> APIResponse:
        """Get login status from local database (no network request)."""
        try:
            # 获取当前会话信息
            session_info = self.cookie_manager.get_current_session_info()
            if not session_info:
                return APIResponse(
                    status=200,
                    body={
                        "code": 401,
                        "message": "没有可用的会话",
                        "data": {"logged_in": False}
                    }
                )

            return APIResponse(
                status=200,
                body={
                    "code": 200,
                    "message": "获取本地登录状态成功",
                    "data": {
                        "logged_in": True,
                        "user_id": session_info.account_id,
                        "nickname": session_info.nickname,
                        "avatar_url": session_info.avatar_url,
                        "session_id": session_info.session_id,
                        "last_success_at": session_info.last_success_at,
                        "session_info": session_info.to_dict()
                    }
                }
            )

        except Exception as e:
            logger.error(f"获取本地登录状态失败: {str(e)}")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"获取本地登录状态失败: {str(e)}",
                    "data": {"logged_in": False}
                }
            )

    # ==================== Helper Methods ====================
    
    async def get_user_info_from_cookie(self, cookie: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Get user info using cookie."""
        try:
            kwargs_with_cookie = {**kwargs, "cookie": cookie}
            status_response = await self.get_login_status(**kwargs_with_cookie)

            if status_response.success:
                data = status_response.body.get("data", {})
                if data.get("logged_in"):
                    return {
                        "user_id": data["user_id"],
                        "nickname": data["nickname"],
                        "avatar_url": data["avatar_url"]
                    }
            return None

        except Exception:
            return None

    async def save_user_login(self, user_info: Dict[str, Any], cookie: str, login_type: str) -> Dict[str, Any]:
        """Save user login info to database."""
        account_id = user_info["user_id"]
        # Create account and session
        with get_session() as session:
            account = self.account_repo.get_account_by_id(session, account_id)
            if not account:
                account = self.account_repo.create_account(
                session=session,
                account_id=account_id,
                nickname=user_info["nickname"],
                avatar_url=user_info["avatar_url"],
            )
            session = self.account_repo.create_session(
                session=session,
                account_id=account_id,
                cookie=cookie,
                login_type=login_type
            )

            result = {
                'account': account.to_dict(),
                'sessions': session.to_dict()
            }
        return result

    async def upload_and_validate_cookie(self, cookie: str, **kwargs) -> Dict[str, Any]:
        """
        Upload and validate cookie business logic.

        Args:
            cookie: Cookie string to upload and validate

        Returns:
            Dict containing validation result and user info
        """
        try:
            # Validate cookie by getting user info
            user_info = await self.get_user_info_from_cookie(cookie, **kwargs)

            if not user_info:
                return {
                    "success": False,
                    "code": 400,
                    "message": "Cookie 无效或已过期"
                }

            # Save user login with cookie
            result = await self.save_user_login(user_info, cookie, "cookie_upload")

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


    async def validate_cookie_only(self, cookie: str, **kwargs) -> Dict[str, Any]:
        """
        Validate cookie without saving to database.

        Args:
            cookie: Cookie string to validate

        Returns:
            Dict containing validation result
        """
        try:
            # Validate cookie by getting user info
            user_info = await self.get_user_info_from_cookie(cookie, **kwargs)

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