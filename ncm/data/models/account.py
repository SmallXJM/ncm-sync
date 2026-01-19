"""Account model definition."""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from ncm.data.engine import Base


class Account(Base):
    """Account model for storing external site account metadata."""
    __tablename__ = 'accounts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String(50), unique=True, nullable=False, index=True)  # External site userId
    nickname = Column(String(100))
    avatar_url = Column(String(500))
    status = Column(String(20), default='active')  # active, disabled, banned
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'account_id': self.account_id,
            'nickname': self.nickname,
            'avatar_url': self.avatar_url,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        """String representation."""
        return f"<Account(account_id='{self.account_id}', nickname='{self.nickname}', status='{self.status}')>"