from __future__ import annotations

from typing import Optional, List
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from ncm.data.models.account_session import AccountSession
from ncm.infrastructure.utils.time import UTC_CLOCK


class AsyncAccountRepository:
    async def get_session_by_id(self, session: AsyncSession, session_id: str) -> Optional[AccountSession]:
        result = await session.execute(select(AccountSession).where(AccountSession.session_id == session_id))
        return result.scalar_one_or_none()

    async def get_valid_sessions_ordered_by_last_selected(self, session: AsyncSession) -> List[AccountSession]:
        result = await session.execute(
            select(AccountSession)
            .where(AccountSession.is_valid == True)
            .order_by(desc(AccountSession.last_selected_at).nulls_last())
        )
        return list(result.scalars().all())

    async def update_session_selected_time(self, session: AsyncSession, session_id: str) -> bool:
        result = await session.execute(select(AccountSession).where(AccountSession.session_id == session_id))
        account_session = result.scalar_one_or_none()
        if not account_session:
            return False
        account_session.last_selected_at = UTC_CLOCK.now()
        await session.flush()
        await session.refresh(account_session)
        return True

    async def mark_session_success(self, session: AsyncSession, session_id: str) -> bool:
        result = await session.execute(select(AccountSession).where(AccountSession.session_id == session_id))
        account_session = result.scalar_one_or_none()
        if not account_session:
            return False
        account_session.last_success_at = UTC_CLOCK.now()
        account_session.fail_count = 0
        await session.flush()
        await session.refresh(account_session)
        return True

    async def mark_session_failure(self, session: AsyncSession, session_id: str, max_failures: int = 3) -> bool:
        result = await session.execute(select(AccountSession).where(AccountSession.session_id == session_id))
        account_session = result.scalar_one_or_none()
        if not account_session:
            return False
        account_session.fail_count = (account_session.fail_count or 0) + 1
        if account_session.fail_count >= max_failures:
            account_session.is_valid = False
        await session.flush()
        await session.refresh(account_session)
        return True

    async def invalidate_session(self, session: AsyncSession, session_id: str) -> bool:
        result = await session.execute(select(AccountSession).where(AccountSession.session_id == session_id))
        account_session = result.scalar_one_or_none()
        if not account_session:
            return False
        account_session.is_valid = False
        await session.flush()
        await session.refresh(account_session)
        return True

