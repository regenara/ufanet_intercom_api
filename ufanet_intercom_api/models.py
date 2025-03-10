from datetime import datetime
from typing import (List,
                    Optional)

from pydantic import BaseModel


class Token(BaseModel):
    access: str
    refresh: str
    exp: int


class Role(BaseModel):
    id: int
    name: str


class Intercom(BaseModel):
    id: int
    contract: Optional[str]
    role: Role
    camera: Optional[str]
    cctv_number: str
    string_view: str
    timeout: int
    disable_button: bool
    no_sound: bool
    open_in_talk: str
    open_type: str
    dtmf_code: str
    inactivity_reason: Optional[str]
    house: int
    frsi: bool
    is_fav: bool
    model: int
    custom_name: Optional[str]
    is_blocked: bool
    supports_key_recording: bool
    ble_support: bool
    scope: str


class HistoryResult(BaseModel):
    uuid: str
    house_id: int
    address: str
    porch: str
    flat: str
    called_at: datetime
    camera_number: str
    skud_mac: str
    timezone: str


class History(BaseModel):
    count: int
    next: Optional[str]
    previous: Optional[str]
    results: List[HistoryResult]


class HistoryData(BaseModel):
    url: str
    preview: str
