"""Integration boundary for a server-side Angel One SmartAPI adapter.

Do not put credentials in Android resources, source control, or client requests.
Implement this module only after validating account entitlement and current SDK APIs.
"""
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class FeedHealth:
    connected: bool
    last_tick_at: datetime | None

    def is_fresh(self, max_age_seconds: int = 120) -> bool:
        if not self.connected or self.last_tick_at is None:
            return False
        ts = self.last_tick_at
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - ts.astimezone(timezone.utc)).total_seconds()
        return 0 <= age <= max_age_seconds
