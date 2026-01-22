"""Profile HTTP controller for user profile and account functionality."""

import logging
from typing import Optional

from ncm.client import APIResponse
from ncm.server.decorators import ncm_service
from ncm.service.cookie import get_cookie_manager

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
            result = await self.cookie_service.get_login_status()
            
            return APIResponse(
                status=200,
                body={
                    "code": 200,
                    "message": "获取用户资料成功",
                    "data": result.profile
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
    async def get_current_account_info(self, **kwargs) -> APIResponse:
        """Get current account information from database."""
        try:
            result = await self.cookie_service.get_current_session()
            
            return APIResponse(
                status=200,
                body={
                    "code": 200,
                    "message": "获取当前账户成功",
                    "data": result
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