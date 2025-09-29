from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class Status(BaseModel):
    pit_temp_c: Optional[float] = None
    meat_temp_1_c: Optional[float] = None
    meat_temp_2_c: Optional[float] = None
    ambient_temp_c: Optional[float] = None
    damper_percent: float
    setpoint_c: float
    meat_setpoint_c: Optional[float] = None
    control_mode: str = "manual"
    safety_shutdown: bool = False
    connected_probes: List[str] = []
    pid_output: float = 0.0
    pid_error: float = 0.0
    timestamp: datetime

    # Legacy compatibility
    meat_temp_c: Optional[float] = None

    def __init__(self, **data):
        # Handle legacy meat_temp_c field
        if 'meat_temp_c' not in data and 'meat_temp_1_c' in data:
            data['meat_temp_c'] = data['meat_temp_1_c']
        elif 'meat_temp_c' in data and 'meat_temp_1_c' not in data:
            data['meat_temp_1_c'] = data['meat_temp_c']
        super().__init__(**data)


class SetpointIn(BaseModel):
    setpoint_c: float = Field(ge=0, le=400)


class MeatSetpointIn(BaseModel):
    meat_setpoint_c: float = Field(ge=0, le=200)


class DamperIn(BaseModel):
    damper_percent: int = Field(ge=0, le=100)


class PIDGainsIn(BaseModel):
    pid_gains: List[float]


class ControlModeIn(BaseModel):
    control_mode: str = Field(pattern=r'^(manual|automatic)$')


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


# Pi-native enhanced schemas
class ProbeStatus(BaseModel):
    probe_name: str
    connected: bool
    last_temp: Optional[float] = None
    last_update: Optional[str] = None
    total_readings: int = 0
    consecutive_errors: int = 0
    min_temp: Optional[float] = None
    max_temp: Optional[float] = None
    average_temp: Optional[float] = None


class SystemStatus(BaseModel):
    probes: Dict[str, ProbeStatus]
    system_enabled: bool = True
    safety_shutdown: bool = False
    control_loop_count: int = 0
    telemetry_points: int = 0
    connected_probes: int = 0


class PIDTuningInfo(BaseModel):
    current_error: float
    error_trend: str
    integral_contribution: float
    derivative_contribution: float
    proportional_contribution: float
    output_percentage: float
    at_output_limit: bool


class PIDPresetLoad(BaseModel):
    preset_name: str = Field(pattern=r'^(conservative|aggressive|precise|slow_cook|high_temp)$')


class ProbeCalibration(BaseModel):
    probe_name: str = Field(pattern=r'^(pit_probe|meat_probe_1|meat_probe_2|ambient_probe)$')
    actual_temperature: float = Field(ge=-40, le=200)


class PerformanceStats(BaseModel):
    pid_controller: Dict
    control_loop_count: int
    telemetry_points: int
    connected_probes: int
    uptime_seconds: float


class TelemetryPoint(BaseModel):
    timestamp: str
    pit_temp_c: Optional[float] = None
    meat_temp_1_c: Optional[float] = None
    meat_temp_2_c: Optional[float] = None
    ambient_temp_c: Optional[float] = None
    setpoint_c: float
    meat_setpoint_c: Optional[float] = None
    damper_percent: float
    pid_output: float
    pid_error: float
    control_mode: str
    safety_shutdown: bool


class EnhancedTelemetryOut(BaseModel):
    points: List[TelemetryPoint]


# CSV Logging schemas
class CSVLoggingStartIn(BaseModel):
    filename: str = Field(min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_\-\.]+$')
    interval_seconds: float = Field(ge=1.0, le=300.0, default=5.0)


class CSVLoggingStatusOut(BaseModel):
    enabled: bool
    file_path: Optional[str] = None
    interval_seconds: float = 0.0
    duration_seconds: float = 0.0
    start_time: Optional[str] = None


class CSVLoggingStopOut(BaseModel):
    file_path: str
    duration_seconds: float
