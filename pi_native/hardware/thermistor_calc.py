import math
from typing import Optional, Dict, NamedTuple
from dataclasses import dataclass
import logging

class SteinhartHartCoefficients(NamedTuple):
    """Steinhart-Hart equation coefficients for thermistor temperature calculation"""
    A: float
    B: float  
    C: float

@dataclass
class ThermistorConfig:
    """Configuration for a thermistor probe"""
    name: str
    resistance_nominal: int  # Nominal resistance at 25°C (usually 10kΩ)
    temperature_nominal: float  # Temperature for nominal resistance (usually 25°C)
    b_coefficient: int  # B coefficient (usually 3950)
    series_resistor: int  # Series resistor value in ohms (usually 10kΩ)
    steinhart_hart: Optional[SteinhartHartCoefficients] = None
    offset_c: float = 0.0  # Calibration offset in Celsius

class ThermistorCalculator:
    """Handles temperature calculations for NTC thermistors"""
    
    # Default configurations for common thermistors
    DEFAULT_CONFIGS = {
        "10K_3950": ThermistorConfig(
            name="10K NTC 3950",
            resistance_nominal=10000,
            temperature_nominal=25.0,
            b_coefficient=3950,
            series_resistor=10000,
            steinhart_hart=SteinhartHartCoefficients(
                A=0.001129148,
                B=0.000234125,
                C=0.0000000876741
            )
        ),
        "10K_3435": ThermistorConfig(
            name="10K NTC 3435", 
            resistance_nominal=10000,
            temperature_nominal=25.0,
            b_coefficient=3435,
            series_resistor=10000,
            steinhart_hart=SteinhartHartCoefficients(
                A=0.001125308852122,
                B=0.000234711863267,
                C=0.000000085663516
            )
        )
    }
    
    def __init__(self, supply_voltage: float = 3.3):
        self.supply_voltage = supply_voltage
        self.probe_configs: Dict[int, ThermistorConfig] = {}
        
        # Set default configuration for all channels
        for channel in range(4):
            self.probe_configs[channel] = self.DEFAULT_CONFIGS["10K_3950"]
    
    def set_probe_config(self, channel: int, config: ThermistorConfig) -> None:
        """Set thermistor configuration for a specific channel"""
        if channel < 0 or channel > 3:
            raise ValueError(f"Invalid channel {channel}. Must be 0-3")
        
        self.probe_configs[channel] = config
        logging.info(f"Channel {channel} configured for {config.name}")
    
    def get_probe_config(self, channel: int) -> ThermistorConfig:
        """Get thermistor configuration for a channel"""
        return self.probe_configs.get(channel, self.DEFAULT_CONFIGS["10K_3950"])
    
    def voltage_to_resistance(self, voltage: float, series_resistor: int) -> float:
        """Convert measured voltage to thermistor resistance using voltage divider"""
        if voltage <= 0.001 or voltage >= self.supply_voltage:
            raise ValueError(f"Invalid voltage {voltage}V (supply: {self.supply_voltage}V)")
        
        # Voltage divider: Vout = Vcc * R_thermistor / (R_series + R_thermistor)
        # Solving for R_thermistor: R_thermistor = R_series * Vout / (Vcc - Vout)
        resistance = series_resistor * self.supply_voltage / voltage - series_resistor
        return resistance
    
    def resistance_to_temperature_beta(self, resistance: float, config: ThermistorConfig) -> float:
        """Convert resistance to temperature using Beta equation (simpler but less accurate)"""
        # Beta equation: T = 1/(1/T0 + (1/B)*ln(R/R0))
        # Where T is in Kelvin, T0 is nominal temp in Kelvin
        
        t0_kelvin = config.temperature_nominal + 273.15
        ln_ratio = math.log(resistance / config.resistance_nominal)
        
        temp_kelvin = 1.0 / (1.0/t0_kelvin + ln_ratio/config.b_coefficient)
        temp_celsius = temp_kelvin - 273.15
        
        return temp_celsius + config.offset_c
    
    def resistance_to_temperature_steinhart_hart(self, resistance: float, config: ThermistorConfig) -> float:
        """Convert resistance to temperature using Steinhart-Hart equation (more accurate)"""
        if not config.steinhart_hart:
            # Fall back to Beta equation if no Steinhart-Hart coefficients
            return self.resistance_to_temperature_beta(resistance, config)
        
        # Steinhart-Hart equation: 1/T = A + B*ln(R) + C*(ln(R))^3
        # Where T is in Kelvin
        
        coeff = config.steinhart_hart
        ln_r = math.log(resistance)
        
        temp_kelvin_inv = coeff.A + coeff.B * ln_r + coeff.C * (ln_r ** 3)
        temp_kelvin = 1.0 / temp_kelvin_inv
        temp_celsius = temp_kelvin - 273.15
        
        return temp_celsius + config.offset_c
    
    def voltage_to_temperature(self, voltage: float, channel: int, use_steinhart_hart: bool = True) -> Optional[float]:
        """Convert ADC voltage directly to temperature for a specific channel"""
        try:
            config = self.get_probe_config(channel)
            
            # Convert voltage to resistance
            resistance = self.voltage_to_resistance(voltage, config.series_resistor)
            
            # Convert resistance to temperature
            if use_steinhart_hart and config.steinhart_hart:
                temperature = self.resistance_to_temperature_steinhart_hart(resistance, config)
            else:
                temperature = self.resistance_to_temperature_beta(resistance, config)
            
            return temperature
            
        except (ValueError, ZeroDivisionError, OverflowError) as e:
            logging.warning(f"Temperature calculation error for channel {channel}: {e}")
            return None
    
    def calibrate_probe(self, channel: int, measured_temp: float, actual_temp: float) -> None:
        """Calibrate a probe by setting offset based on known temperature"""
        config = self.get_probe_config(channel)
        config.offset_c = actual_temp - measured_temp
        logging.info(f"Channel {channel} calibrated with offset {config.offset_c:.2f}°C")
    
    def get_temperature_range(self, config: ThermistorConfig) -> tuple[float, float]:
        """Get practical temperature range for a thermistor configuration"""
        # Calculate temps at voltage extremes (with some margin)
        min_voltage = 0.1  # Minimum readable voltage
        max_voltage = self.supply_voltage - 0.1  # Maximum voltage (leaving margin)
        
        try:
            min_resistance = self.voltage_to_resistance(max_voltage, config.series_resistor)
            max_resistance = self.voltage_to_resistance(min_voltage, config.series_resistor)
            
            min_temp = self.resistance_to_temperature_steinhart_hart(max_resistance, config)
            max_temp = self.resistance_to_temperature_steinhart_hart(min_resistance, config)
            
            return (min_temp, max_temp)
            
        except Exception:
            # Fallback to typical range for NTC thermistors
            return (-40.0, 150.0)

    def validate_reading(self, temperature: float, channel: int) -> bool:
        """Validate if temperature reading is within reasonable range"""
        config = self.get_probe_config(channel)
        min_temp, max_temp = self.get_temperature_range(config)
        
        return min_temp <= temperature <= max_temp
