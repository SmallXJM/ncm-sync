"""User management business logic orchestration."""

from typing import Dict, Any, List, Optional
from ncm.infrastructure.db import AccountRepository
from ncm.infrastructure.db.session import get_session
from ncm.service.cookie import get_cookie_manager
from ncm.core.logging import get_logger

logger = get_logger(__name__)


class UserManagementService:
    """Business logic for user management workflows."""

    def __init__(self):
        """Initialize user management service."""
        self.account_repo = AccountRepository()
        self.cookie_manager = get_cookie_manager()

    def get_current_account_info(self) -> Dict[str, Any]:
        """
        Get current logged in account from database.
        
        Returns:
            Dict containing current account information
        """
        try:
            session_info = self.cookie_manager.get_current_session_info()
            if not session_info:
                return {
                    "success": True,
                    "code": 404,
                    "message": "没有当前登录账户",
                    "data": None
                }

            with get_session() as session:
                account = self.account_repo.get_account_by_id(session, session_info.account_id)
                # logger.info(account)
                if not account:
                    return {
                        "success": True,
                        "code": 404,
                        "message": "账户信息不存在",
                        "data": None
                    }

                # Convert to dict while session is active
                account_dict = account.to_dict()

            return {
                "success": True,
                "code": 200,
                "message": "获取当前账户信息成功",
                "data": {
                    "account": {
                        **account_dict,
                        "status": "active",
                    },
                    "session": {
                        "session_id": session_info.session_id,
                        "login_type": session_info.login_type,
                        "is_valid": session_info.is_valid,
                        "last_success_at": session_info.last_success_at.isoformat() if session_info.last_success_at else None,
                        "last_selected_at": session_info.last_selected_at.isoformat() if session_info.last_selected_at else None,
                    }
                }
            }

        except Exception as e:
            logger.exception(f"获取当前账户信息失败: {str(e)}")
            return {
                "success": False,
                "code": 500,
                "message": f"获取当前账户信息失败: {str(e)}"
            }

    def list_all_accounts(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        List all accounts with pagination.
        
        Args:
            limit: Maximum number of accounts to return
            offset: Number of accounts to skip
            
        Returns:
            Dict containing list of accounts
        """
        try:
            with get_session() as session:
                accounts = self.account_repo.get_all_accounts_with_sessions(session)

                # Apply pagination
                total_count = len(accounts)
                paginated_accounts = accounts[offset:offset + limit]

            account_list = []
            for account_info in paginated_accounts:
                account = account_info['account']
                sessions = account_info['sessions']

                # Count valid sessions
                valid_sessions = [s for s in sessions if s['is_valid']]

                account_dict = {
                    "account_id": account["account_id"],
                    "nickname": account["nickname"],
                    "avatar_url": account["avatar_url"],
                    "created_at": account["created_at"],
                    "updated_at": account["updated_at"],
                    "session_count": len(sessions),
                    "valid_session_count": len(valid_sessions),
                    "last_login": max([s["last_success_at"] for s in sessions if s["last_success_at"]], default=None)
                }
                account_list.append(account_dict)

            return {
                "success": True,
                "code": 200,
                "message": f"获取账户列表成功，共 {total_count} 个账户",
                "data": {
                    "accounts": account_list,
                    "pagination": {
                        "total": total_count,
                        "limit": limit,
                        "offset": offset,
                        "has_more": offset + limit < total_count
                    }
                }
            }

        except Exception as e:
            logger.error(f"获取账户列表失败: {str(e)}")
            return {
                "success": False,
                "code": 500,
                "message": f"获取账户列表失败: {str(e)}"
            }

    def switch_to_session(self, session_id: str) -> Dict[str, Any]:
        """
        Switch to a different session (set as current session).
        
        Args:
            session_id: Target session ID to switch to
            
        Returns:
            Dict containing switch result
        """
        try:
            success = self.cookie_manager.force_switch_to_session(session_id)

            if success:
                # Get updated session info
                session_info = self.cookie_manager.get_current_session_info()

                return {
                    "success": True,
                    "code": 200,
                    "message": "切换会话成功",
                    "data": {
                        "current_session_id": session_id,
                        "session_info": session_info
                    }
                }
            else:
                return {
                    "success": False,
                    "code": 400,
                    "message": "切换会话失败，会话可能不存在或已失效"
                }

        except Exception as e:
            logger.error(f"切换会话失败: {str(e)}")
            return {
                "success": False,
                "code": 500,
                "message": f"切换会话失败: {str(e)}"
            }

    def list_all_sessions(self) -> Dict[str, Any]:
        """
        List all sessions with current session marked.
        
        Returns:
            Dict containing list of sessions
        """
        try:
            sessions = self.cookie_manager.list_all_sessions()
            current_session_id = self.cookie_manager.get_current_session_id()

            return {
                "success": True,
                "code": 200,
                "message": f"获取会话列表成功，共 {len(sessions)} 个会话",
                "data": {
                    "sessions": [s.to_dict() for s in sessions if s.is_valid],
                    "current_session_id": current_session_id,
                    "total_sessions": len(sessions),
                    "valid_sessions": len([s for s in sessions if s.is_valid])
                }
            }

        except Exception as e:
            logger.exception(f"获取会话列表失败: {str(e)}")
            return {
                "success": False,
                "code": 500,
                "message": f"获取会话列表失败: {str(e)}"
            }

    def invalidate_session(self, session_id: str) -> Dict[str, Any]:
        """
        Manually invalidate a session.
        
        Args:
            session_id: Session ID to invalidate
            
        Returns:
            Dict containing invalidation result
        """
        try:
            success = self.cookie_manager.invalidate_session(session_id)

            if success:
                return {
                    "success": True,
                    "code": 200,
                    "message": "会话失效成功"
                }
            else:
                return {
                    "success": False,
                    "code": 400,
                    "message": "会话失效失败，会话可能不存在"
                }

        except Exception as e:
            logger.error(f"会话失效失败: {str(e)}")
            return {
                "success": False,
                "code": 500,
                "message": f"会话失效失败: {str(e)}"
            }

    def delete_account(self, account_id: str) -> Dict[str, Any]:
        """
        Delete an account and all associated sessions.
        
        Args:
            account_id: Account ID to delete
            
        Returns:
            Dict containing deletion result
        """
        try:
            with get_session() as session:
                # Check if account exists
                account = self.account_repo.get_account_by_id(session, account_id)
                if not account:
                    return {
                        "success": False,
                        "code": 404,
                        "message": "账户不存在"
                    }

                # Delete account and all associated sessions
                success = self.account_repo.delete_account(session, account_id)

            if success:
                # If the deleted account was current, switch to another
                current_session = self.cookie_manager.get_current_session_info()
                if current_session and current_session.account_id == account_id:
                    self.cookie_manager._select_next_available_session()

                return {
                    "success": True,
                    "code": 200,
                    "message": "账户删除成功"
                }
            else:
                return {
                    "success": False,
                    "code": 500,
                    "message": "账户删除失败"
                }

        except Exception as e:
            logger.error(f"删除账户失败: {str(e)}")
            return {
                "success": False,
                "code": 500,
                "message": f"删除账户失败: {str(e)}"
            }
