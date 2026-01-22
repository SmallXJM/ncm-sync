"""
Cookie management business logic.

Refactored to be simple and direct, using only AccountSession and _login_status_cache.
"""

import logging
import asyncio
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from ncm.data.async_session import get_uow_factory
from ncm.data.repositories.async_account_session_repo import AsyncAccountSessionRepository
from ncm.data.models.account_session import AccountSession
from ncm.client.apis.user import login
from ncm.core.time import UTC_CLOCK
from ncm.service.cookie.models import SimpleSession
from ncm.client.apis.user.login.models import LoginStatusResponse



logger = logging.getLogger(__name__)



class CookieManager:
    """
    Cookie Manager
    
    Manages the current session and login status cache.
    """

    def __init__(self):
        self._async_repo = AsyncAccountSessionRepository()
        self._uow_factory = get_uow_factory()

        # Current session ID (referencing database ID)
        self._current_session: Optional[AccountSession] = None

        # Cache of the full response from login.status()
        self._login_status_cache: Optional[LoginStatusResponse] = None

        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """
        Initialize the manager.
        Selects the last selected valid session, verifies it, and caches the status.
        """
        try:
            async with self._uow_factory() as uow:
                sessions = await self._async_repo.get_valid_sessions_ordered_by_last_selected(uow.session)

                if not sessions:
                    logger.warning("No valid sessions found during initialization.")
                    return

                # Pick the most recently selected one
                session = sessions[0]
                logger.info(f"Initializing with session ID: {session.id} (user_id: {session.account_id})")

                # Verify and cache status
                resp = await login.status(cookie=session.cookie)

                if resp.success and resp.body.get("code") == 200:
                    self._login_status_cache = LoginStatusResponse.model_validate(resp.body)
                    self._current_session = session

                    # Update selection time
                    await self._async_repo.update_session_selected_time(uow.session, session.id)
                    await uow.commit()

                    logger.info(f"{self._login_status_cache.profile.nickname}: {session.account_id} initialized and verified.")
                else:
                    logger.warning(f"user_id: {session.account_id} failed verification during initialization.")
                    data = resp.body.get("data", {})
                    if data.get("account"):
                        self._login_status_cache = LoginStatusResponse.model_validate(resp.body)
                        self._current_session = session
                        await self._async_repo.update_session_selected_time(uow.session, session.id)
                        await uow.commit()
                        logger.info(f"{self._login_status_cache.profile.nickname}: {session.account_id} re-initialized and verified.")
                    else:
                        logger.warning(f"Session {session.id} appears to be expired or invalid (no account data).")
                        self._login_status_cache = LoginStatusResponse.model_validate(resp.body)

        except Exception as e:
            logger.error(f"Initialization failed: {str(e)}")

    async def add_session(self, cookie: str, login_type: str = 'manual') -> Dict[str, Any]:
        """
        Add a new session (cookie).
        Validates the cookie first. If valid, saves it and sets it as current.
        """
        async with self._lock:
            # 1. Validate cookie
            resp = await login.status(cookie=cookie)
            if not resp.success:
                raise ValueError("Failed to connect to NCM API for validation")

            body = resp.body
            data = body.get("data", {})
            account = data.get("account")

            if not account:
                raise ValueError("Cookie is invalid or expired (no account info)")

            account_id = str(account.get("id"))

            # 2. Save to database
            async with self._uow_factory() as uow:
                new_session = await self._async_repo.create_session(
                    uow.session,
                    account_id=account_id,
                    cookie=cookie,
                    login_type=login_type,
                )
                await uow.commit()

                session_id = new_session.id
                session_dict = new_session.to_dict()

            # 3. Set as current
            self._current_session = new_session
            self._login_status_cache = LoginStatusResponse.model_validate(body)

            logger.info(f"Added and switched to new session {session_id} for account {self._login_status_cache.profile.nickname}")

            return session_dict

    def get_current_session_id(self) -> Optional[int]:
        """Return the ID of the current session."""
        return self._current_session.id if self._current_session else None
    
    def get_login_status(self) -> Optional[LoginStatusResponse]:
        """Return the cached login status."""
        return self._login_status_cache

    async def refresh_status(self) -> Optional[LoginStatusResponse]:
        """Force refresh the status of the current session."""
        if not self._current_session:
            return None

        session = self._current_session

        resp = await login.status(cookie=session.cookie)
        if resp.success:
            self._login_status_cache = LoginStatusResponse.model_validate(resp.body)
            logger.info(f"Refreshed status for account {self._login_status_cache.profile.nickname}")    
            return self._login_status_cache
        return None

    async def list_sessions(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List all sessions with pagination."""
        try:
            async with self._uow_factory() as uow:
                sessions = await self._async_repo.get_all_sessions(uow.session, limit, offset)
                return [s.to_dict() for s in sessions]
        except Exception as e:
            logger.error(f"List sessions failed: {str(e)}")
            return []

    async def switch_to_session(self, session_id: int) -> bool:
        """Switch current session to the specified session ID."""
        try:
            async with self._uow_factory() as uow:
                session = await self._async_repo.get_session_by_id(uow.session, session_id)
                if not session or not session.is_valid:
                    return False

                self._current_session = session
                await self._async_repo.update_session_selected_time(uow.session, session.id)
                await uow.commit()

                await self.refresh_status()
                return True
        except Exception as e:
            logger.error(f"Switch session failed: {str(e)}")
            return False

    async def invalidate_session(self, session_id: int) -> bool:
        """Invalidate a session."""
        try:
            async with self._uow_factory() as uow:
                success = await self._async_repo.invalidate_session(uow.session, session_id)
                await uow.commit()

                if success and self._current_session and self._current_session.id == session_id:
                    self._current_session = None
                    self._login_status_cache = None

                    # Try to pick a new valid session
                    await self.initialize()

                return success
        except Exception as e:
            logger.error(f"Invalidate session failed: {str(e)}")
            return False

    # Helpers for decorators
    async def get_current_session(self) -> Optional[SimpleSession]:
        if not self._current_session:
            return None
        session = self._current_session
        if session:
            return SimpleSession(id=session.id, user_id=session.account_id, cookie=session.cookie, login_type=session.login_type)
        return None

    async def mark_cookie_success(self) -> None:
        if not self._current_session:
            return
        try:
            async with self._uow_factory() as uow:
                await self._async_repo.mark_session_success(uow.session, self._current_session.id)
                await uow.commit()
        except Exception as e:
            logger.error(f"Mark success failed: {str(e)}")

    async def mark_cookie_failure(self) -> None:
        if not self._current_session:
            return
        try:
            async with self._uow_factory() as uow:
                await self._async_repo.mark_session_failure(uow.session, self._current_session.id)
                await uow.commit()

                # Check if still valid
                logger.warning(f"Session {self._current_session.id} invalidated due to failures. Switching...")
                self._current_session = None
                self._login_status_cache = None
                await self.initialize()
        except Exception as e:
            logger.error(f"Mark failure failed: {str(e)}")


# Singleton instance
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
