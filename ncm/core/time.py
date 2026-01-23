from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from tzlocal import get_localzone
from typing import Protocol, Optional

class Clock(Protocol):
    def now(self) -> datetime: ...

class SystemUTCClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)

UTC_CLOCK: Clock = SystemUTCClock()


def to_iso_format(dt: Optional[datetime]) -> Optional[str]:
    """Format datetime to ISO string with UTC timezone (handling naive datetimes from SQLite)."""
    if not dt:
        return None
    # SQLite stores naive datetimes (implied UTC), so we must attach timezone
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


class Timezone(Protocol):
    def get(self) -> ZoneInfo: ...
    
class SystemTimezone:
    def get(self) -> ZoneInfo:
        try:
            return get_localzone()
        except Exception:
            return ZoneInfo("Asia/Shanghai")  # 兜底

TIMEZONE_SYSTEM: Timezone = SystemTimezone()

