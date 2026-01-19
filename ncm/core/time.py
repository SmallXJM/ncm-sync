from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from tzlocal import get_localzone
from typing import Protocol

class Clock(Protocol):
    def now(self) -> datetime: ...

class SystemUTCClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)

UTC_CLOCK: Clock = SystemUTCClock()


class Timezone(Protocol):
    def get(self) -> ZoneInfo: ...
    
class SystemTimezone:
    def get(self) -> ZoneInfo:
        try:
            return get_localzone()
        except Exception:
            return ZoneInfo("Asia/Shanghai")  # 兜底

TIMEZONE_SYSTEM: Timezone = SystemTimezone()

