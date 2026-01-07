"""
Cookie management business logic.

专为单实例 NAS Docker 服务设计：
- 程序启动时选择一个 Cookie，持续使用直到失效
- 失效时自动选择下一个可用 Cookie
- 内存缓存当前 Cookie，避免频繁数据库查询
- 重启后根据 last_selected_at 恢复上次使用的 Cookie
"""

import logging
from typing import Optional, List
from datetime import datetime
from ncm.infrastructure.db import AccountRepository
from ncm.infrastructure.db.session import get_session
from ncm.infrastructure.db.async_session import get_uow_factory
from ncm.infrastructure.db.repositories.async_account_repo import AsyncAccountRepository
from ncm.service.cookie.models import SessionInfo

logger = logging.getLogger(__name__)





class CookieManager:
    """
    Cookie 管理业务逻辑
    
    核心原则：
    1. 一次选择，持续使用 - 程序运行期间使用同一个 Cookie
    2. 失效时自动切换 - 当前 Cookie 失效时选择下一个可用的
    3. 内存缓存 - 避免频繁数据库查询
    4. 持久化选择 - 重启后恢复上次使用的 Cookie
    """

    def __init__(self):
        self.account_repo = AccountRepository()
        self._async_repo = AsyncAccountRepository()
        self._uow_factory = get_uow_factory()

        # 当前会话（SessionInfo 对象）
        self._current_session: Optional[SessionInfo] = None
        self._last_check_time: Optional[datetime] = None

        self._initialize_current_session()

    # ======================
    # 初始化与选择逻辑
    # ======================
    def _initialize_current_session(self) -> None:
        try:
            with get_session() as session:
                sessions = self.account_repo.get_valid_sessions_ordered_by_last_selected(session)
                if not sessions:
                    logger.warning("没有可用的会话，需要先登录")
                    return

                # 转换为 SessionInfo 对象
                session_info = SessionInfo.from_orm(sessions[0])
                self._set_current_session(session_info, update_selected_time=True)
                logger.info(
                    f"恢复使用会话: {session_info.session_id} "
                    f"(账户: {session_info.account_id})"
                )
        except Exception as e:
            logger.error(f"初始化会话失败: {str(e)}")

    def _set_current_session(self, session_info: SessionInfo, *, update_selected_time: bool):
        self._current_session = session_info
        self._last_check_time = datetime.now()

        if update_selected_time:
            with get_session() as db_session:
                self.account_repo.update_session_selected_time(db_session, session_info.session_id)

    # ======================
    # 对外访问接口
    # ======================
    def get_current_session(self) -> Optional[SessionInfo]:
        """
        获取当前会话（完整信息，来自内存）
        """
        if self._current_session:
            return self._current_session

        self._select_next_available_session()
        return self._current_session

    def get_current_cookie(self) -> Optional[str]:
        """
        向后兼容接口
        """
        session = self.get_current_session()
        return session.cookie if session else None

    def get_current_session_id(self) -> Optional[str]:
        session = self.get_current_session()
        return session.session_id if session else None

    # ======================
    # 成功 / 失败标记
    # ======================
    async def mark_cookie_success(self) -> bool:
        if not self._current_session:
            return False
        try:
            async with self._uow_factory() as uow:
                success = await self._async_repo.mark_session_success(
                    uow.session, self._current_session.session_id
                )
                if success:
                    logger.debug(f"会话成功: {self._current_session.session_id}")
                return success
        except Exception as e:
            logger.error(f"标记[会话成功]失败: {str(e)}")
            return False

    async def mark_cookie_failure(self, max_failures: int = 3) -> bool:
        if not self._current_session:
            return False
        sid = self._current_session.session_id
        try:
            async with self._uow_factory() as uow:
                success = await self._async_repo.mark_session_failure(uow.session, sid, max_failures)
                if success:
                    logger.warning(f"会话失败: {sid}")
                    updated_session = await self._async_repo.get_session_by_id(uow.session, sid)
                    if updated_session and not updated_session.is_valid:
                        logger.warning(f"会话已失效，切换下一个: {sid}")
                        self._select_next_available_session()
                return success
        except Exception as e:
            logger.error(f"标记[会话失败]失败: {str(e)}")
            return False

    # ======================
    # 会话切换
    # ======================
    def _select_next_available_session(self) -> bool:
        try:
            with get_session() as session:
                sessions = self.account_repo.get_valid_sessions_ordered_by_last_selected(session)

                available = [
                    s for s in sessions
                    if not self._current_session
                    or s.session_id != self._current_session.session_id
                ]

                if not available:
                    self._current_session = None
                    logger.error("没有可用的会话")
                    return False

                # 转换为 SessionInfo 对象
                session_info = SessionInfo.from_orm(available[0])
                self._set_current_session(session_info, update_selected_time=True)

                logger.info(
                    f"切换到新会话: {session_info.session_id} "
                    f"(账户: {session_info.account_id})"
                )
                return True

        except Exception as e:
            logger.error(f"切换会话失败: {str(e)}")
            return False

    # ======================
    # 管理接口
    # ======================
    def force_switch_to_session(self, session_id: str) -> bool:
        try:
            with get_session() as session:
                account_session = self.account_repo.get_session_by_id(session, session_id)
                if not account_session or not account_session.is_valid:
                    return False

                session_info = SessionInfo.from_orm(account_session)
                self._set_current_session(session_info, update_selected_time=True)
                logger.info(f"强制切换会话: {session_id}")
                return True
        except Exception as e:
            logger.error(f"强制切换失败: {str(e)}")
            return False

    def list_all_sessions(self) -> List[SessionInfo]:
        try:
            with get_session() as session:
                sessions_with_accounts = self.account_repo.get_all_sessions_with_accounts(session)
                result = []

                for info in sessions_with_accounts:
                    account_session = info["session"]
                    account = info["account"]

                    # 创建 SessionInfo 对象并合并账户信息
                    session_info = SessionInfo.from_orm(account_session, account)
                    session_info.is_current = (
                        self._current_session
                        and session_info.session_id == self._current_session.session_id
                    )
                    result.append(session_info)

                return result
        except Exception as e:
            logger.exception(f"列出会话失败: {str(e)}")
            return []

    def get_current_session_info(self) -> Optional[SessionInfo]:
        """获取当前会话的详细信息"""
        current_session = self.get_current_session()
        if not current_session:
            return None

        try:
            with get_session() as session:
                account = self.account_repo.get_account_by_id(session, current_session.account_id)
                if not account:
                    return current_session

                # 创建新的 SessionInfo 对象，合并账户信息
                session_info = SessionInfo.from_orm_with_account_data(
                    current_session, account.nickname, account.avatar_url
                )
                return session_info
        except Exception as e:
            logger.error(f"获取会话信息失败: {str(e)}")
            return current_session

    def invalidate_session(self, session_id: str) -> bool:
        """手动失效会话"""
        try:
            with get_session() as session:
                success = self.account_repo.invalidate_session(session, session_id)
                
                # 如果失效的是当前会话，需要切换
                if success and self._current_session and self._current_session.session_id == session_id:
                    self._select_next_available_session()
                
                return success
        except Exception as e:
            logger.error(f"失效会话失败: {str(e)}")
            return False


# 全局单例实例
_cookie_manager_instance: Optional[CookieManager] = None


def get_cookie_manager() -> CookieManager:
    """
    获取 CookieManager 单例实例
        
    Returns:
        CookieManager 实例
    """
    global _cookie_manager_instance

    if _cookie_manager_instance is None:
        _cookie_manager_instance = CookieManager()

    return _cookie_manager_instance
