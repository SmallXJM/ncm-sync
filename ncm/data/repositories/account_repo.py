"""Account repository using SQLAlchemy ORM."""

import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy import desc, and_
from sqlalchemy.orm import Session
from ncm.core.time import UTC_CLOCK
from ..models.account import Account
from ..models.account_session import AccountSession


class AccountRepository:
    """Repository for account and session operations."""
    
    def __init__(self):
        """Initialize repository."""
        pass
    
    # Account operations
    def create_account(self, session: Session, account_id: str, nickname: str = None, avatar_url: str = None) -> Account:
        """Create a new account."""
        account = Account(
            account_id=account_id,
            nickname=nickname,
            avatar_url=avatar_url,
            status='active'
        )
        
        session.add(account)
        session.flush()
        session.refresh(account)
        return account
    
    def get_account_by_id(self, session: Session, account_id: str) -> Optional[Account]:
        """Get account by account_id."""
        return session.query(Account).filter(Account.account_id == account_id).first()
    
    def update_account(self, session: Session, account_id: str, nickname: str = None, avatar_url: str = None, 
                      status: str = None) -> Optional[Account]:
        """Update account information."""
        account = session.query(Account).filter(Account.account_id == account_id).first()
        if not account:
            return None
        
        if nickname is not None:
            account.nickname = nickname
        if avatar_url is not None:
            account.avatar_url = avatar_url
        if status is not None:
            account.status = status
        
        session.flush()
        session.refresh(account)
        return account
    
    def list_accounts(self, session: Session, limit: int = 100, offset: int = 0) -> List[Account]:
        """List all accounts with pagination."""
        return (session.query(Account)
               .order_by(desc(Account.updated_at))
               .offset(offset)
               .limit(limit)
               .all())
    
    def delete_account(self, session: Session, account_id: str) -> bool:
        """Delete account and all its sessions."""
        # Delete all sessions first
        session.query(AccountSession).filter(AccountSession.account_id == account_id).delete()
        
        # Delete account
        account = session.query(Account).filter(Account.account_id == account_id).first()
        if not account:
            return False
        
        session.delete(account)
        return True
    
    # Session operations
    def create_session(self, session: Session, account_id: str, cookie: str, login_type: str = 'qr') -> AccountSession:
        """Create a new session for an account."""
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Create new session
        account_session = AccountSession(
            session_id=session_id,
            account_id=account_id,
            cookie=cookie,
            login_type=login_type,
            is_valid=True,
            fail_count=0,
            last_selected_at=UTC_CLOCK.now(),  # Set as current immediately
            last_success_at=UTC_CLOCK.now()
        )
        
        session.add(account_session)
        session.flush()
        session.refresh(account_session)
        return account_session
    
    def get_current_session(self, session: Session) -> Optional[AccountSession]:
        """Get current session (most recently selected valid session)."""
        return (session.query(AccountSession)
                      .filter(AccountSession.is_valid == True)
                      .order_by(desc(AccountSession.last_selected_at).nulls_last())
                      .first())
    
    def get_session_by_id(self, session: Session, session_id: str) -> Optional[AccountSession]:
        """Get session by session_id."""
        return session.query(AccountSession).filter(AccountSession.session_id == session_id).first()
    
    def get_sessions_by_account(self, session: Session, account_id: str) -> List[AccountSession]:
        """Get all sessions for an account."""
        return (session.query(AccountSession)
               .filter(AccountSession.account_id == account_id)
               .order_by(desc(AccountSession.created_at))
               .all())
    
    def get_valid_sessions(self, session: Session) -> List[AccountSession]:
        """Get all valid sessions."""
        return (session.query(AccountSession)
               .filter(AccountSession.is_valid == True)
               .order_by(desc(AccountSession.last_selected_at).nulls_last())
               .all())
    
    def get_valid_sessions_ordered_by_last_selected(self, session: Session) -> List[AccountSession]:
        """Get all valid sessions ordered by last_selected_at (most recent first)."""
        return (session.query(AccountSession)
               .filter(AccountSession.is_valid == True)
               .order_by(desc(AccountSession.last_selected_at).nulls_last())
               .all())
    
    def get_all_sessions_with_accounts(self, session: Session) -> List[Dict[str, Any]]:
        """Get all sessions with their associated account information."""
        sessions = (session.query(AccountSession)
                   .order_by(desc(AccountSession.id).nulls_last())
                   .all())
        
        result = []
        for sess in sessions:
            account = session.query(Account).filter(Account.account_id == sess.account_id).first()
            result.append({
                'session': sess,
                'account': account
            })
        
        return result
    
    def get_all_accounts_with_sessions(self, session: Session) -> List[Dict[str, Any]]:
        """Get all accounts with their associated sessions."""
        accounts = session.query(Account).order_by(desc(Account.updated_at)).all()
        
        result = []
        for account in accounts:
            sessions = (session.query(AccountSession)
                       .filter(AccountSession.account_id == account.account_id)
                       .order_by(desc(AccountSession.created_at))
                       .all())
            
            result.append({
                'account': account,
                'sessions': sessions
            })
        
        return result
    
    def update_session_selected_time(self, session: Session, session_id: str) -> bool:
        """Update the last_selected_at time for a session."""
        account_session = session.query(AccountSession).filter(AccountSession.session_id == session_id).first()
        
        if not account_session:
            return False
        account_session.last_selected_at = UTC_CLOCK.now()
        return True
    
    def select_session(self, session: Session, session_id: str) -> bool:
        """Select a session as current (update last_selected_at)."""
        account_session = session.query(AccountSession).filter(
            and_(AccountSession.session_id == session_id, AccountSession.is_valid == True)
        ).first()
        
        if not account_session:
            return False
        account_session.last_selected_at = UTC_CLOCK.now()
        return True
    
    def mark_session_success(self, session: Session, session_id: str) -> bool:
        """Mark session as successful (reset fail_count, update last_success_at)."""
        account_session = session.query(AccountSession).filter(AccountSession.session_id == session_id).first()
        
        if not account_session:
            return False
        account_session.last_success_at = UTC_CLOCK.now()
        account_session.fail_count = 0
        return True
    
    def mark_session_failure(self, session: Session, session_id: str, max_failures: int = 3) -> bool:
        """Mark session as failed (increment fail_count, invalidate if threshold reached)."""
        account_session = session.query(AccountSession).filter(AccountSession.session_id == session_id).first()
        
        if not account_session:
            return False
        
        account_session.fail_count += 1
        
        # Invalidate if failure threshold reached
        if account_session.fail_count >= max_failures:
            account_session.is_valid = False
        
        return True
    
    def invalidate_session(self, session: Session, session_id: str) -> bool:
        """Manually invalidate a session."""
        account_session = session.query(AccountSession).filter(AccountSession.session_id == session_id).first()
        
        if not account_session:
            return False
        
        account_session.is_valid = False
        return True
    
    def delete_session(self, session: Session, session_id: str) -> bool:
        """Delete a session."""
        account_session = session.query(AccountSession).filter(AccountSession.session_id == session_id).first()
        
        if not account_session:
            return False
        
        session.delete(account_session)
        return True
