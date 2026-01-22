"""Management HTTP controller for user and session management functionality."""

import logging
from ncm.client import APIResponse
from ncm.server.decorators import ncm_service
from ncm.service.cookie import get_cookie_manager

logger = logging.getLogger(__name__)


class SessionController:
    """HTTP controller for user and session management functionality."""
    
    def __init__(self):
        """Initialize management controller."""
        self.cookie_service = get_cookie_manager()

    # ==================== Session Management ====================
    @ncm_service("/ncm/user/session/current", ["GET"])
    async def get_current_account_info(self, **kwargs) -> APIResponse:
        """Get current account information from database."""
        try:
            result = await self.cookie_service.get_current_session()
            
            if result:
                return APIResponse(
                    status=200,
                    body={
                        "code": 200,
                        "message": "获取当前账户成功",
                        "data": result.to_dict()
                    }
                )
            else:
                return APIResponse(
                    status=401,
                    body={
                        "code": 401,
                        "message": "没有可用的账户",
                    }
                )
            
        except Exception as e:
            logger.error(f"获取当前账户失败: {str(e)}")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"获取当前账户失败: {str(e)}"
                }
            )
    
    
    @ncm_service("/ncm/user/session/switch", ["POST"])
    async def switch_session(self, id: int, **kwargs) -> APIResponse:
        """Switch to a different session (set as current session)."""
        try:
            # Use service to switch
            result = await self.cookie_service.switch_to_session(id)
            
            if result:
                return APIResponse(
                    status=200,
                    body={
                        "code": 200,
                        "message": "切换会话成功",
                    }
                )
            else:
                return APIResponse(
                    status=401,
                    body={
                        "code": 401,
                        "message": "切换会话失败"
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
            
    
    @ncm_service("/ncm/user/session/upload", ["POST"])
    async def upload_cookie(self, cookie: str, **kwargs) -> APIResponse:
        """Upload and validate cookie directly."""
        try:
            result = await self.cookie_service.add_session(
                cookie, **kwargs
            )
            
            return APIResponse(
                status=200,
                body={
                    "code": 200,
                    "message": "Cookie 上传成功",
                    "data": result
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

    @ncm_service("/ncm/user/session/invalidate", ["POST"])
    async def invalidate_session(self, id: int, **kwargs) -> APIResponse:
        """Manually invalidate a session."""
        try:
            result = await self.cookie_service.invalidate_session(id)
            
            return APIResponse(
                status=200 if result else 401,
                body={
                    "code": 200 if result else 401,
                    "message": "会话失效成功" if result else "会话不存在",
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
    async def list_all_sessions(self, **kwargs) -> APIResponse:
        """List all sessions with current session marked."""
        try:
            result = await self.cookie_service.list_sessions()
            
            return APIResponse(
                status=200,
                body={
                    "code": 200,
                    "message": "获取会话列表成功",
                    "data": result
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