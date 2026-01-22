from __future__ import annotations

from typing import Optional, List
from sqlalchemy import select, desc, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from ncm.data.models.account_session import AccountSession
from ncm.core.time import UTC_CLOCK


class AsyncAccountSessionRepository:
    """Async repository for session operations."""

    async def create_session(self, session: AsyncSession, account_id: str, cookie: str, login_type: str = 'qr') -> AccountSession:
        """Create a new session."""
        
        account_session = AccountSession(
            account_id=account_id,
            cookie=cookie,
            login_type=login_type,
            is_valid=True,
            fail_count=0,
            last_selected_at=UTC_CLOCK.now(),
            last_success_at=UTC_CLOCK.now()
        )
        
        session.add(account_session)
        await session.flush()
        await session.refresh(account_session)
        return account_session

    async def get_session_by_id(self, session: AsyncSession, session_id: int) -> Optional[AccountSession]:
        """Get session by session_id."""
        result = await session.execute(select(AccountSession).where(AccountSession.id == session_id))
        return result.scalar_one_or_none()

    async def get_current_session(self, session: AsyncSession) -> Optional[AccountSession]:
        """Get current session (most recently selected valid session)."""
        result = await session.execute(
            select(AccountSession)
            .where(AccountSession.is_valid == True)
            .order_by(desc(AccountSession.last_selected_at).nulls_last())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_sessions_by_account(self, session: AsyncSession, account_id: str) -> List[AccountSession]:
        """Get all sessions for an account."""
        result = await session.execute(
            select(AccountSession)
            .where(AccountSession.account_id == account_id)
            .order_by(desc(AccountSession.created_at))
        )
        return list(result.scalars().all())

    async def get_all_sessions(self, session: AsyncSession, limit: int = 100, offset: int = 0) -> List[AccountSession]:
        """Get all sessions with pagination."""
        result = await session.execute(
            select(AccountSession)
            .order_by(desc(AccountSession.id).nulls_last())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_valid_sessions_ordered_by_last_selected(self, session: AsyncSession) -> List[AccountSession]:
        """Get all valid sessions ordered by last_selected_at."""
        result = await session.execute(
            select(AccountSession)
            .where(AccountSession.is_valid == True)
            .order_by(desc(AccountSession.last_selected_at).nulls_last())
        )
        return list(result.scalars().all())

    async def update_session_selected_time(self, session: AsyncSession, session_id: int) -> bool:
        """Update the last_selected_at time for a session."""
        result = await session.execute(select(AccountSession).where(AccountSession.id == session_id))
        account_session = result.scalar_one_or_none()
        if not account_session:
            return False
        account_session.last_selected_at = UTC_CLOCK.now()
        await session.flush()
        await session.refresh(account_session)
        return True
    
    async def select_session(self, session: AsyncSession, session_id: int) -> bool:
        """Select a session as current (update last_selected_at)."""
        result = await session.execute(
            select(AccountSession).where(
                and_(AccountSession.id == session_id, AccountSession.is_valid == True)
            )
        )
        account_session = result.scalar_one_or_none()
        
        if not account_session:
            return False
        account_session.last_selected_at = UTC_CLOCK.now()
        await session.flush()
        return True

    async def mark_session_success(self, session: AsyncSession, session_id: int) -> bool:
        """Mark session as successful."""
        result = await session.execute(select(AccountSession).where(AccountSession.id == session_id))
        account_session = result.scalar_one_or_none()
        if not account_session:
            return False
        account_session.last_success_at = UTC_CLOCK.now()
        account_session.fail_count = 0
        await session.flush()
        await session.refresh(account_session)
        return True

    async def mark_session_failure(self, session: AsyncSession, session_id: int, max_failures: int = 3) -> bool:
        """Mark session as failed."""
        result = await session.execute(select(AccountSession).where(AccountSession.id == session_id))
        account_session = result.scalar_one_or_none()
        if not account_session:
            return False
        account_session.fail_count = (account_session.fail_count or 0) + 1
        if account_session.fail_count >= max_failures:
            account_session.is_valid = False
        await session.flush()
        await session.refresh(account_session)
        return True

    async def invalidate_session(self, session: AsyncSession, session_id: int) -> bool:
        """Manually invalidate a session."""
        result = await session.execute(select(AccountSession).where(AccountSession.id == session_id))
        account_session = result.scalar_one_or_none()
        if not account_session:
            return False
        account_session.is_valid = False
        await session.flush()
        await session.refresh(account_session)
        return True
    
    async def delete_session(self, session: AsyncSession, session_id: int) -> bool:
        """Delete a session."""
        result = await session.execute(select(AccountSession).where(AccountSession.id == session_id))
        account_session = result.scalar_one_or_none()
        if not account_session:
            return False
        await session.delete(account_session)
        await session.flush()
        return True
