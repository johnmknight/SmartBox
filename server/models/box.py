# server/models/box.py
from pydantic import BaseModel
from typing import Optional

class BoxState(BaseModel):
    box_id: str
    rack_id: Optional[str] = None
    display_name: Optional[str] = None
    state: Optional[str] = None
    category: Optional[str] = None
    battery_pct: Optional[float] = None
    battery_v: Optional[float] = None
    charging: Optional[bool] = None
    wifi_rssi: Optional[int] = None
    firmware: Optional[str] = None
    last_seen: Optional[str] = None

class BoxCommand(BaseModel):
    action: str  # identify | set_category | set_mode | reboot
    category: Optional[str] = None
    mode: Optional[str] = None
    countdown: Optional[int] = None
