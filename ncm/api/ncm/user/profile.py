"""Profile HTTP controller for user profile and account functionality."""

import logging
from typing import Optional

from ncm.service.user import UserManagementService
from ncm.client import APIResponse
from ncm.infrastructure.http import ncm_service
from ncm.infrastructure.db import AccountRepository
from ncm.infrastructure.db.session import get_session
from ncm.service.cookie import get_cookie_manager

logger = logging.getLogger(__name__)


class ProfileController:
    """HTTP controller for user profile and account functionality."""
    
    def __init__(self):
        """Initialize profile controller."""
        self.account_repo = AccountRepository()
        self.cookie_service = get_cookie_manager()
        self.user_service = UserManagementService()

    # ==================== Profile Management ====================
    
    @ncm_service("/ncm/user/profile", ["GET", "POST"])
    async def get_user_profile(self, account_id: Optional[str] = None, **kwargs) -> APIResponse:
        """Get user profile with enhanced information."""
        try:
            # If no account_id provided, get current account
            if not account_id:
                current_info = self.cookie_service.get_current_session_info()
                if not current_info:
                    return APIResponse(
                        status=400,
                        body={
                            "code": 400,
                            "message": "未找到当前登录用户"
                        }
                    )
                account_id = current_info.account_id
            
            with get_session() as session:
                # Get account from database
                account = self.account_repo.get_account_by_id(session, account_id)
                if not account:
                    return APIResponse(
                        status=404,
                        body={
                            "code": 404,
                            "message": f"用户 {account_id} 不存在"
                        }
                    )
            
                # Get current session info
                session_info = self.cookie_service.get_current_session_info()

                # Get login status from API if has valid session
                login_status = None
                if session_info and session_info.account_id == account_id:
                    try:
                        # Import here to avoid circular import
                        from .auth import AuthController
                        auth_controller = AuthController()
                        login_status_response = await auth_controller.get_login_status(**kwargs)
                        if login_status_response.success:
                            login_status = login_status_response.body.get("data", {})
                    except Exception:
                        # If API call fails, user might be logged out
                        login_status = {"logged_in": False}

                return APIResponse(
                    status=200,
                    body={
                        "code": 200,
                        "message": "获取用户资料成功",
                        "data": {
                            "account": account.to_dict(),
                            "session_info": session_info.to_dict(),
                            "login_status": login_status,
                            "has_valid_session": login_status and login_status.get("logged_in", False)
                        }
                    }
                )
            
        except Exception as e:
            logger.error(f"获取用户资料失败: {str(e)}")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"获取用户资料失败: {str(e)}"
                }
            )
    
    @ncm_service("/ncm/user/current", ["GET"])
    def get_current_account_info(self, **kwargs) -> APIResponse:
        """Get current account information from database."""
        try:
            result = self.user_service.get_current_account_info()
            
            return APIResponse(
                status=200 if result["success"] else result.get("code", 500),
                body={
                    "code": result["code"],
                    "message": result["message"],
                    "data": result.get("data")
                }
            )
            
        except Exception as e:
            logger.exception(f"获取当前用户信息失败: {str(e)}")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"获取当前用户信息失败: {str(e)}"
                }
            )
    
    @ncm_service("/ncm/user/update", ["PUT"])
    def update_account_info(self, account_id: str, nickname: Optional[str] = None, 
                           avatar_url: Optional[str] = None) -> APIResponse:
        """Update account information."""
        try:
            with get_session() as session:
                account = self.account_repo.get_account_by_id(session, account_id)
                if not account:
                    return APIResponse(
                        status=404,
                        body={
                            "code": 404,
                            "message": f"用户 {account_id} 不存在"
                        }
                    )
                
                # Update account
                updated_account = self.account_repo.update_account(
                    session=session,
                    account_id=account_id,
                    nickname=nickname,
                    avatar_url=avatar_url
                )
            
            return APIResponse(
                status=200,
                body={
                    "code": 200,
                    "message": "用户信息已更新",
                    "data": {
                        "account": updated_account.to_dict()
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"更新用户信息失败: {str(e)}")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"更新用户信息失败: {str(e)}"
                }
            )

    # ==================== Account Management ====================
    
    def logout_account(self, account_id: str) -> APIResponse:
        """Logout account by invalidating all sessions."""
        try:
            with get_session() as session:
                sessions = self.account_repo.get_sessions_by_account(session, account_id)
                if not sessions:
                    return APIResponse(
                        status=200,
                        body={
                            "code": 404,
                            "message": f"账户 {account_id} 没有会话"
                        }
                    )
            
            success_count = 0
            for session in sessions:
                if self.cookie_service.invalidate_session(session.session_id):
                    success_count += 1
            
            return APIResponse(
                status=200,
                body={
                    "code": 200,
                    "message": f"已注销 {success_count}/{len(sessions)} 个会话",
                    "data": {
                        "invalidated_sessions": success_count,
                        "total_sessions": len(sessions)
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"注销账户失败: {str(e)}")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"注销账户失败: {str(e)}"
                }
            )