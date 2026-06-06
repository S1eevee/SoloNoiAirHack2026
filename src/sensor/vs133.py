"""
Milesight VS133-P AI ToF People Counting Sensor — payload parser.

Supports both HTTP push and MQTT delivery.
The sensor may use slightly different field names depending on firmware version;
normalize() returns a canonical dict regardless.
"""
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel


class VS133Payload(BaseModel):
    device_eui: str
    timestamp: Optional[int] = None       # unix ms or unix s — auto-detected
    zone: str = "checkin"                 # "checkin" or "security"

    # Firmware variant A
    people_count_in: int = 0
    people_count_out: int = 0

    # Firmware variant B (line-based)
    line1_in: Optional[int] = None
    line1_out: Optional[int] = None

    def normalize(self) -> dict:
        count_in = self.people_count_in or self.line1_in or 0
        count_out = self.people_count_out or self.line1_out or 0

        ts = self.timestamp or int(datetime.now(timezone.utc).timestamp() * 1000)
        # Milliseconds if > year 3000 in seconds
        ts_dt = (
            datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
            if ts > 1_000_000_000_000
            else datetime.fromtimestamp(ts, tz=timezone.utc)
        )

        return {
            "device_eui": self.device_eui,
            "timestamp": ts_dt,
            "zone": self.zone,
            "count_in": count_in,
            "count_out": count_out,
        }
