"""Account session model definition."""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from ncm.core.time import UTC_CLOCK, to_iso_format
from ncm.data.engine import Base


class AccountSession(Base):
    """Account session model for storing cookies and session state."""
    __tablename__ = 'account_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String(50), nullable=False, index=True)
    cookie = Column(Text, nullable=False)  # NCM session cookie
    login_type = Column(String(20), nullable=False)  # qr, phone, email, cookie_upload
    is_valid = Column(Boolean, default=True)  # Whether still usable
    fail_count = Column(Integer, default=0)  # Consecutive failure count
    last_selected_at = Column(DateTime)  # Last time selected as current cookie
    last_success_at = Column(DateTime)  # Last successful request time
    expired_at = Column(DateTime)  # Known expiration time (nullable)
    created_at = Column(DateTime, default=lambda: UTC_CLOCK.now())
    updated_at = Column(DateTime, default=lambda: UTC_CLOCK.now(), onupdate=lambda: UTC_CLOCK.now())
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'account_id': self.account_id,
            'has_cookie': bool(self.cookie),
            'cookie': self.cookie,
            'login_type': self.login_type,
            'is_valid': self.is_valid,
            'fail_count': self.fail_count,
            'last_selected_at': to_iso_format(self.last_selected_at),
            'last_success_at': to_iso_format(self.last_success_at),
            'expired_at': to_iso_format(self.expired_at),
            'created_at': to_iso_format(self.created_at),
            'updated_at': to_iso_format(self.updated_at),
        }
    
    def __repr__(self):
        """String representation."""
        return f"<AccountSession(id={self.id}, account_id='{self.account_id}', login_type='{self.login_type}', is_valid={self.is_valid})>"