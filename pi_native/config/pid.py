"""PID controller configuration for Pi-native EggBot"""

from dataclasses import dataclass, field
from typing import Dict, Tuple

@dataclass
class PIDGains:
    """PID controller gain values"""
    kp: float  # Proportional gain
    ki: float  # Integral gain  
    kd: float  # Derivative gain
    
    def as_tuple(self) -> Tuple[float, float, float]:
        return (self.kp, self.ki, self.kd)

@dataclass
class PIDLimits:
    """PID controller limits and constraints"""
    output_min: float = 0.0      # Minimum output value (0% damper)
    output_max: float = 100.0    # Maximum output value (100% damper)
    integral_min: float = -50.0  # Integral windup limit (negative)
    integral_max: float = 50.0   # Integral windup limit (positive)
    derivative_filter: float = 0.1  # Low-pass filter for derivative term (0-1)

@dataclass
class PIDConfig:
    """Complete PID configuration"""
    gains: PIDGains
    limits: PIDLimits = field(default_factory=PIDLimits)
    sample_time: float = 1.0     # Control loop period in seconds
    auto_mode: bool = True       # Start in automatic mode
    
# Predefined PID tuning presets for different cooking scenarios
PID_PRESETS = {
    "conservative": PIDConfig(
        gains=PIDGains(kp=2.0, ki=0.1, kd=1.0),
        limits=PIDLimits(
            output_min=0.0,
            output_max=100.0,
            integral_min=-20.0,
            integral_max=20.0,
            derivative_filter=0.2
        ),
        sample_time=2.0
    ),
    
    "aggressive": PIDConfig(
        gains=PIDGains(kp=4.0, ki=0.3, kd=2.0),
        limits=PIDLimits(
            output_min=0.0,
            output_max=100.0,
            integral_min=-30.0,
            integral_max=30.0,
            derivative_filter=0.1
        ),
        sample_time=1.0
    ),
    
    "precise": PIDConfig(
        gains=PIDGains(kp=3.0, ki=0.2, kd=1.5),
        limits=PIDLimits(
            output_min=0.0,
            output_max=100.0,
            integral_min=-25.0,
            integral_max=25.0,
            derivative_filter=0.15
        ),
        sample_time=1.0
    ),
    
    "slow_cook": PIDConfig(
        gains=PIDGains(kp=1.5, ki=0.05, kd=0.8),
        limits=PIDLimits(
            output_min=0.0,
            output_max=80.0,  # Limited range for slow cooking
            integral_min=-15.0,
            integral_max=15.0,
            derivative_filter=0.3
        ),
        sample_time=3.0
    ),
    
    "high_temp": PIDConfig(
        gains=PIDGains(kp=5.0, ki=0.4, kd=2.5),
        limits=PIDLimits(
            output_min=0.0,
            output_max=100.0,
            integral_min=-40.0,
            integral_max=40.0,
            derivative_filter=0.08
        ),
        sample_time=0.5
    )
}

@dataclass
class SafetyLimits:
    """Safety limits for temperature control"""
    max_pit_temp: float = 400.0     # Maximum pit temperature (°C)
    min_pit_temp: float = 50.0      # Minimum pit temperature (°C)  
    max_meat_temp: float = 100.0    # Maximum meat temperature (°C)
    min_meat_temp: float = 0.0      # Minimum meat temperature (°C)
    
    # Emergency shutdown conditions
    temp_rate_limit: float = 10.0   # Max °C/minute temperature rise
    probe_timeout: float = 30.0     # Seconds before probe considered disconnected
    max_damper_time: float = 300.0  # Max seconds damper can stay 100% open
    
    # Warning thresholds
    high_temp_warning: float = 350.0  # °C
    probe_disconnect_warning: float = 15.0  # Seconds

@dataclass  
class ControlConfig:
    """Complete control system configuration"""
    pid: PIDConfig
    safety: SafetyLimits = field(default_factory=SafetyLimits)
    
    # Control loop timing
    main_loop_interval: float = 0.25   # Seconds between sensor readings
    control_loop_interval: float = 1.0  # Seconds between PID calculations
    telemetry_interval: float = 5.0     # Seconds between telemetry logging
    
    # Temperature filtering
    temp_filter_alpha: float = 0.3      # Low-pass filter coefficient (0-1)
    temp_change_threshold: float = 0.5  # °C minimum change to trigger update
    
    # Auto-tuning parameters
    autotune_enabled: bool = False
    autotune_noise_band: float = 0.5    # °C
    autotune_setpoint_offset: float = 2.0  # °C above setpoint for tuning

# Default control configuration
default_control_config = ControlConfig(
    pid=PID_PRESETS["conservative"],
    safety=SafetyLimits()
)