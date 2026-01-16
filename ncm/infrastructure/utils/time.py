from datetime import datetime, timezone
from typing import Protocol

class Clock(Protocol):
    def now(self) -> datetime: ...

class SystemUTCClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)

UTC_CLOCK: Clock = SystemUTCClock()
