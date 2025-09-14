"""Hardware configuration for Pi-native EggBot"""

from dataclasses import dataclass, field
from typing import Dict
from pi_native.hardware.thermistor_calc import ThermistorConfig, SteinhartHartCoefficients

@dataclass
class GPIOConfig:
    """GPIO pin assignments"""
    servo_pin: int = 18          # PWM-capable pin for servo control
    i2c_sda_pin: int = 2         # I2C SDA (GPIO 2)
    i2c_scl_pin: int = 3         # I2C SCL (GPIO 3)
    led_status_pin: int = 16     # Optional status LED
    led_error_pin: int = 20      # Optional error LED

@dataclass 
class ADCConfig:
    """ADS1115 ADC configuration"""
    i2c_address: int = 0x48      # Default ADS1115 I2C address
    supply_voltage: float = 3.3   # ADC reference voltage
    sample_rate: int = 860       # Samples per second (128, 250, 490, 920, 1600, 2400, 3300)
    gain: int = 1                # PGA gain (1, 2, 4, 8, 16)
    
@dataclass
class ServoConfig:
    """Servo motor configuration"""
    min_pulse_width: int = 1033  # Microseconds for 48° position (closed damper)
    max_pulse_width: int = 1833  # Microseconds for 120° position (open damper)
    center_pulse_width: int = 1433  # Microseconds for 84° position (center)
    pwm_frequency: int = 50      # Hz
    max_speed: float = 30.0      # Degrees per second
    position_tolerance: float = 2.0  # Degrees

# Default thermistor configurations
THERMISTOR_CONFIGS = {
    "pit_probe": ThermistorConfig(
        name="Pit Temperature Probe",
        resistance_nominal=10000,
        temperature_nominal=25.0,
        b_coefficient=3950,
        series_resistor=10000,
        steinhart_hart=SteinhartHartCoefficients(
            A=0.0007343140544,
            B=0.0002157437229, 
            C=0.0000000951568577
        ),
        offset_c=0.0
    ),
    
    "meat_probe_1": ThermistorConfig(
        name="Meat Probe 1",
        resistance_nominal=10000,
        temperature_nominal=25.0,
        b_coefficient=3950,
        series_resistor=10000,
        steinhart_hart=SteinhartHartCoefficients(
            A=0.0007343140544,
            B=0.0002157437229, 
            C=0.0000000951568577
        ),
        offset_c=0.0
    ),
    
    "meat_probe_2": ThermistorConfig(
        name="Meat Probe 2", 
        resistance_nominal=10000,
        temperature_nominal=25.0,
        b_coefficient=3950,
        series_resistor=10000,
        steinhart_hart=SteinhartHartCoefficients(
            A=0.0007343140544,
            B=0.0002157437229, 
            C=0.0000000951568577
        ),
        offset_c=0.0
    ),
    
    "ambient_probe": ThermistorConfig(
        name="Ambient Temperature Probe",
        resistance_nominal=10000,
        temperature_nominal=25.0,
        b_coefficient=3950,
        series_resistor=10000,
        steinhart_hart=SteinhartHartCoefficients(
            A=0.0007343140544,
            B=0.0002157437229, 
            C=0.0000000951568577
        ),
        offset_c=0.0
    )
}

# Channel mapping for temperature probes
PROBE_CHANNEL_MAP = {
    0: "pit_probe",        # Channel 0 = Pit temperature
    1: "meat_probe_1",     # Channel 1 = First meat probe  
    2: "meat_probe_2",     # Channel 2 = Second meat probe
    3: "ambient_probe"     # Channel 3 = Ambient temperature
}

# Reverse mapping for convenience
CHANNEL_PROBE_MAP = {v: k for k, v in PROBE_CHANNEL_MAP.items()}

@dataclass
class HardwareConfig:
    """Complete hardware configuration"""
    gpio: GPIOConfig = field(default_factory=GPIOConfig)
    adc: ADCConfig = field(default_factory=ADCConfig)
    servo: ServoConfig = field(default_factory=ServoConfig)
    thermistors: Dict[str, ThermistorConfig] = None
    
    def __post_init__(self):
        if self.thermistors is None:
            self.thermistors = THERMISTOR_CONFIGS.copy()
    
    def get_probe_config(self, channel: int) -> ThermistorConfig:
        """Get thermistor config for a specific ADC channel"""
        probe_name = PROBE_CHANNEL_MAP.get(channel)
        if not probe_name:
            raise ValueError(f"Invalid channel {channel}")
        
        return self.thermistors[probe_name]
    
    def set_probe_config(self, channel: int, config: ThermistorConfig) -> None:
        """Set thermistor config for a specific ADC channel"""
        probe_name = PROBE_CHANNEL_MAP.get(channel)
        if not probe_name:
            raise ValueError(f"Invalid channel {channel}")
        
        self.thermistors[probe_name] = config
    
    def get_channel_for_probe(self, probe_name: str) -> int:
        """Get ADC channel number for a probe name"""
        channel = CHANNEL_PROBE_MAP.get(probe_name)
        if channel is None:
            raise ValueError(f"Unknown probe name: {probe_name}")
        return channel

# Global hardware configuration instance
hardware_config = HardwareConfig()
