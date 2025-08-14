from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Status(BaseModel):
    pit_temp_c: float
    meat_temp_c: Optional[float] = None
    damper_percent: int
    setpoint_c: float
    timestamp: datetime

class SetpointIn(BaseModel):
    setpoint_c: float = Field(ge=0, le=400)

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
    
