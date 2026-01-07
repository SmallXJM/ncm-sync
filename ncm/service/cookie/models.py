from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


@dataclass
class SessionInfo:
    """会话信息数据类"""
    session_id: str
    account_id: str
    cookie: str
    login_type: str
    is_valid: bool
    last_success_at: Optional[datetime]
    last_selected_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    # 扩展信息（从 Account 合并）
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    is_current: bool = False

    def to_dict(self):
        """转换为字典，用于 API 返回，自动序列化 datetime"""
        data = asdict(self)
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data

    @classmethod
    def from_orm(cls, session_orm, account_orm=None) -> 'SessionInfo':
        """从 ORM 对象创建"""
        return cls(
            session_id=session_orm.session_id,
            account_id=session_orm.account_id,
            cookie=session_orm.cookie,
            login_type=session_orm.login_type,
            is_valid=session_orm.is_valid,
            last_success_at=session_orm.last_success_at,
            last_selected_at=session_orm.last_selected_at,
            created_at=session_orm.created_at,
            updated_at=session_orm.updated_at,
            nickname=account_orm.nickname if account_orm else None,
            avatar_url=account_orm.avatar_url if account_orm else None,
        )

    @classmethod
    def from_orm_with_account_data(cls, session_info: 'SessionInfo', nickname: str, avatar_url: str) -> 'SessionInfo':
        """从现有 SessionInfo 创建新对象，合并账户数据"""
        return cls(
            session_id=session_info.session_id,
            account_id=session_info.account_id,
            cookie=session_info.cookie,
            login_type=session_info.login_type,
            is_valid=session_info.is_valid,
            last_success_at=session_info.last_success_at,
            last_selected_at=session_info.last_selected_at,
            created_at=session_info.created_at,
            updated_at=session_info.updated_at,
            nickname=nickname,
            avatar_url=avatar_url,
            is_current=session_info.is_current,
        )