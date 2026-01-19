"""Account session model definition."""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from ..engine import Base


class AccountSession(Base):
    """Account session model for storing cookies and session state."""
    __tablename__ = 'account_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)  # Internal session identifier
    account_id = Column(String(50), ForeignKey('accounts.account_id'), nullable=False, index=True)
    cookie = Column(Text, nullable=False)  # NCM session cookie
    login_type = Column(String(20), nullable=False)  # qr, phone, email, cookie_upload
    is_valid = Column(Boolean, default=True)  # Whether still usable
    fail_count = Column(Integer, default=0)  # Consecutive failure count
    last_selected_at = Column(DateTime)  # Last time selected as current cookie
    last_success_at = Column(DateTime)  # Last successful request time
    expired_at = Column(DateTime)  # Known expiration time (nullable)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'account_id': self.account_id,
            'has_cookie': bool(self.cookie),
            'cookie': self.cookie,
            'login_type': self.login_type,
            'is_valid': self.is_valid,
            'fail_count': self.fail_count,
            'last_selected_at': self.last_selected_at.isoformat() if self.last_selected_at else None,
            'last_success_at': self.last_success_at.isoformat() if self.last_success_at else None,
            'expired_at': self.expired_at.isoformat() if self.expired_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        """String representation."""
        return f"<AccountSession(session_id='{self.session_id}', account_id='{self.account_id}', login_type='{self.login_type}', is_valid={self.is_valid})>"