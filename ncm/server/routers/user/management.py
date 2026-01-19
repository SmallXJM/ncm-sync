"""Management HTTP controller for user and session management functionality."""

import logging
from ncm.service.user import UserManagementService
from ncm.client import APIResponse
from ncm.server.decorators import ncm_service
from ncm.data import AccountRepository
from ncm.data.session import get_session
from ncm.service.cookie import get_cookie_manager

logger = logging.getLogger(__name__)


class ManagementController:
    """HTTP controller for user and session management functionality."""
    
    def __init__(self):
        """Initialize management controller."""
        self.account_repo = AccountRepository()
        self.cookie_service = get_cookie_manager()
        self.user_service = UserManagementService()

    # ==================== Account Management ====================
    
    @ncm_service("/ncm/user/list", ["GET"])
    def list_accounts(self, limit: int = 100, offset: int = 0) -> APIResponse:
        """List all accounts with pagination."""
        try:
            result = self.user_service.list_all_accounts(limit, offset)
            
            return APIResponse(
                status=200 if result["success"] else result.get("code", 500),
                body={
                    "code": result["code"],
                    "message": result["message"],
                    "data": result.get("data")
                }
            )
            
        except Exception as e:
            logger.error(f"获取用户列表失败: {str(e)}")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"获取用户列表失败: {str(e)}"
                }
            )
    
    @ncm_service("/ncm/user/delete", ["DELETE"])
    def delete_account(self, account_id: str) -> APIResponse:
        """Delete an account and all associated sessions."""
        try:
            result = self.user_service.delete_account(account_id)
            
            return APIResponse(
                status=200 if result["success"] else result.get("code", 500),
                body={
                    "code": result["code"],
                    "message": result["message"],
                    "data": result.get("data")
                }
            )
            
        except Exception as e:
            logger.error(f"删除用户失败: {str(e)}")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"删除用户失败: {str(e)}"
                }
            )

    # ==================== Session Management ====================
    
    @ncm_service("/ncm/user/switch", ["POST"])
    async def switch_session(self, session_id: str, **kwargs) -> APIResponse:
        """Switch to a different session (set as current session)."""
        try:
            with get_session() as session:
                session_obj = self.account_repo.get_session_by_id(session, session_id)
                if not session_obj:
                    return APIResponse(
                        status=404,
                        body={
                            "code": 404,
                            "message": f"会话 {session_id} 不存在"
                        }
                    )
                
                if not session_obj.is_valid:
                    return APIResponse(
                        status=400,
                        body={
                            "code": 400,
                            "message": "会话已失效"
                        }
                    )
            
                # Verify the session is still valid with API
                from .auth import AuthController
                auth_controller = AuthController()
                kwargs_with_cookie = {"cookie": session_obj.cookie}
                login_status_response = await auth_controller.get_login_status(**kwargs_with_cookie)
                
                login_status = None
                if login_status_response.success:
                    login_status = login_status_response.body.get("data", {})
                
                if not login_status or not login_status.get("logged_in", False):
                    # Mark session as invalid
                    self.cookie_service.invalidate_session(session_id)
                    return APIResponse(
                        status=400,
                        body={
                            "code": 400,
                            "message": "会话已过期"
                        }
                    )
                
                # Use service service to switch
                result = self.user_service.switch_to_session(session_id)
                
                if result["success"]:
                    # Get account info
                    with get_session() as db_session:
                        account = self.account_repo.get_account_by_id(db_session, session_obj.account_id)
                    
                        return APIResponse(
                            status=200,
                            body={
                                "code": 200,
                                "message": f"已切换到用户 {account.nickname or account.account_id}",
                                "data": {
                                    "account": account.to_dict(),
                                    "session_info": self.cookie_service.get_current_session_info().to_dict(),
                                    "login_status": login_status
                                }
                            }
                        )
                else:
                    return APIResponse(
                        status=result.get("code", 500),
                        body={
                            "code": result["code"],
                            "message": result["message"]
                        }
                    )
            
        except Exception as e:
            logger.exception(f"切换会话失败: {str(e)}")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"切换会话失败: {str(e)}"
                }
            )
    
    @ncm_service("/ncm/user/sessions", ["GET"])
    def list_account_sessions(self, account_id: str, **kwargs) -> APIResponse:
        """List all sessions for an account."""
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
                
                sessions = self.account_repo.get_sessions_by_account(session, account_id)
            
            return APIResponse(
                status=200,
                body={
                    "code": 200,
                    "message": "获取会话列表成功",
                    "data": {
                        "account": account,
                        "sessions": sessions,
                        "session_count": len(sessions),
                        "valid_sessions": len([s for s in sessions if s.is_valid])
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"获取会话列表失败: {str(e)}")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"获取会话列表失败: {str(e)}"
                }
            )
    
    @ncm_service("/ncm/user/session/invalidate", ["POST"])
    def invalidate_session(self, session_id: str, **kwargs) -> APIResponse:
        """Manually invalidate a session."""
        try:
            result = self.user_service.invalidate_session(session_id)
            
            return APIResponse(
                status=200 if result["success"] else result.get("code", 500),
                body={
                    "code": result["code"],
                    "message": result["message"],
                    "data": result.get("data", {"session_id": session_id})
                }
            )
            
        except Exception as e:
            logger.error(f"会话失效操作失败: {str(e)}")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"会话失效操作失败: {str(e)}"
                }
            )
    
    @ncm_service("/ncm/user/sessions/list", ["GET"])
    def list_all_sessions(self, **kwargs) -> APIResponse:
        """List all sessions with current session marked."""
        try:
            result = self.user_service.list_all_sessions()
            
            return APIResponse(
                status=200 if result["success"] else result.get("code", 500),
                body={
                    "code": result["code"],
                    "message": result["message"],
                    "data": result.get("data")
                }
            )
            
        except Exception as e:
            logger.error(f"获取会话列表失败: {str(e)}")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"获取会话列表失败: {str(e)}"
                }
            )