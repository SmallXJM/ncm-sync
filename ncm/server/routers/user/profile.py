"""Profile HTTP controller for user profile and account functionality."""

import logging
from typing import Optional

from ncm.client import APIResponse
from ncm.server.decorators import ncm_service
from ncm.service.cookie import get_cookie_manager, with_cookie

logger = logging.getLogger(__name__)


class ProfileController:
    """HTTP controller for user profile and account functionality."""
    
    def __init__(self):
        """Initialize profile controller."""
        self.cookie_service = get_cookie_manager()

    # ==================== Profile Management ====================
    
    @ncm_service("/ncm/user/profile", ["GET", "POST"])
    async def get_user_profile(self, account_id: Optional[str] = None, **kwargs) -> APIResponse:
        """Get user profile with enhanced information."""
        try:
            result = self.cookie_service.get_login_status()
            
            if result:
                return APIResponse(
                    status=200,
                    body={
                        "code": 200,
                        "message": "获取用户资料成功",
                        "data": result.profile.model_dump(),
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
            logger.error(f"获取用户资料失败: {str(e)}")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"获取用户资料失败: {str(e)}"
                }
            )
    
    # ==================== Login Status ====================
    
    @ncm_service("/ncm/user/status", ["GET", "POST"])
    @with_cookie
    async def get_login_status(self, **kwargs) -> APIResponse:
        """Get current login status using available cookie."""
        try:
            # 使用 refresh_status 获取最新状态
            login_status = await self.cookie_service.refresh_status()
            
            if login_status:
                return APIResponse(
                    status=200,
                    body={
                        "code": 200,
                        "message": "获取登录状态成功",
                        "data": login_status.model_dump(),
                    }
                )
            else:
                return APIResponse(
                    status=401,
                    body={
                        "code": 401,
                        "message": "没有可用的会话",
                    }
                )

        except Exception as e:
            logger.error(f"获取登录状态失败: {str(e)}")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"获取登录状态失败: {str(e)}",
                }
            )