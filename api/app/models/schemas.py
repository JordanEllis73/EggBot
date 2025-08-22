from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Status(BaseModel):
    pit_temp_c: float
    meat_temp_c: Optional[float] = None
    damper_percent: int
    setpoint_c: float
    meat_setpoint_c: Optional[float] = None
    timestamp: datetime


class SetpointIn(BaseModel):
    setpoint_c: float = Field(ge=0, le=400)


class MeatSetpointIn(BaseModel):
    meat_setpoint_c: float = Field(ge=0, le=200)


class DamperIn(BaseModel):
    damper_percent: int = Field(ge=0, le=100)


class PIDGainsIn(BaseModel):
    pid_gains: List[float]


class PIDPreset(BaseModel):
    name: str
    gains: List[float]


class SavePresetRequest(BaseModel):
    name: str
    gains: List[float]


class TelemetryOut(BaseModel):
    points: List[Status]


class MeaterConnectIn(BaseModel):
    address: str = Field(min_length=17, max_length=17, pattern=r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')


class MeaterData(BaseModel):
    probe_temp_c: float
    probe_temp_f: float
    ambient_temp_c: float
    ambient_temp_f: float
    battery_percent: int
    address: str
    firmware: str
    id: str


class MeaterStatus(BaseModel):
    is_connected: bool
    is_connecting: bool
    is_scanning: bool
    address: Optional[str] = None
    last_update: Optional[str] = None
    data: Optional[MeaterData] = None


class MeaterDeviceList(BaseModel):
    devices: List[str]
