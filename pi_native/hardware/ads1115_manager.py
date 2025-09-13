import time
import threading
from typing import Optional, List, Dict
from dataclasses import dataclass
import logging

try:
    import board
    import busio
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
    HARDWARE_AVAILABLE = True
except ImportError:
    HARDWARE_AVAILABLE = False
    logging.warning("ADS1115 hardware libraries not available - running in simulation mode")

@dataclass
class ProbeReading:
    channel: int
    voltage: float
    raw_value: int
    timestamp: float

class ADS1115Manager:
    """Manages I2C communication with ADS1115 ADC for temperature probe readings"""
    
    def __init__(self, i2c_address: int = 0x48, simulate: bool = False):
        self.i2c_address = i2c_address
        self.simulate = simulate or not HARDWARE_AVAILABLE
        self._lock = threading.Lock()
        self._adc = None
        self._channels: Dict[int, AnalogIn] = {}
        self._last_readings: Dict[int, ProbeReading] = {}
        
        if not self.simulate:
            self._initialize_hardware()
        
        logging.info(f"ADS1115Manager initialized (simulate={self.simulate})")
    
    def _initialize_hardware(self) -> None:
        """Initialize I2C connection and ADS1115"""
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            self._adc = ADS.ADS1115(i2c, address=self.i2c_address)
            
            # Initialize all 4 channels
            for i in range(4):
                channel_pin = getattr(ADS, f'P{i}')
                self._channels[i] = AnalogIn(self._adc, channel_pin)
            
            logging.info(f"ADS1115 initialized on I2C address 0x{self.i2c_address:02x}")
            
        except Exception as e:
            logging.error(f"Failed to initialize ADS1115: {e}")
            self.simulate = True
            logging.warning("Falling back to simulation mode")
    
    def read_channel(self, channel: int) -> Optional[ProbeReading]:
        """Read voltage from specified channel (0-3)"""
        if channel < 0 or channel > 3:
            raise ValueError(f"Invalid channel {channel}. Must be 0-3")
        
        with self._lock:
            if self.simulate:
                return self._simulate_reading(channel)
            
            try:
                analog_in = self._channels[channel]
                voltage = analog_in.voltage
                raw_value = analog_in.value
                
                reading = ProbeReading(
                    channel=channel,
                    voltage=voltage,
                    raw_value=raw_value,
                    timestamp=time.time()
                )
                
                self._last_readings[channel] = reading
                return reading
                
            except Exception as e:
                logging.error(f"Error reading channel {channel}: {e}")
                return None
    
    def _simulate_reading(self, channel: int) -> ProbeReading:
        """Simulate ADC reading for testing without hardware"""
        # Simulate different voltage levels for each channel
        base_voltages = [1.5, 1.8, 2.1, 2.4]  # Different thermistor temps
        voltage = base_voltages[channel] + (time.time() % 10) * 0.01  # Small variation
        
        # Simulate 16-bit ADC (0-65535 for 0-3.3V range)
        raw_value = int((voltage / 3.3) * 65535)
        
        return ProbeReading(
            channel=channel,
            voltage=voltage,
            raw_value=raw_value,
            timestamp=time.time()
        )
    
    def read_all_channels(self) -> Dict[int, ProbeReading]:
        """Read all 4 channels and return as dictionary"""
        readings = {}
        for channel in range(4):
            reading = self.read_channel(channel)
            if reading:
                readings[channel] = reading
        return readings
    
    def get_last_reading(self, channel: int) -> Optional[ProbeReading]:
        """Get the last reading for a channel without triggering new read"""
        with self._lock:
            return self._last_readings.get(channel)
    
    def is_channel_connected(self, channel: int, min_voltage: float = 0.1) -> bool:
        """Check if a probe appears to be connected to the channel"""
        reading = self.read_channel(channel)
        if not reading:
            return False
        
        # If voltage is too low, assume no probe connected
        return reading.voltage > min_voltage
    
    def get_connected_channels(self) -> List[int]:
        """Return list of channels that appear to have probes connected"""
        connected = []
        for channel in range(4):
            if self.is_channel_connected(channel):
                connected.append(channel)
        return connected
    
    def close(self) -> None:
        """Clean up resources"""
        if self._adc and not self.simulate:
            try:
                # ADS1115 doesn't require explicit cleanup, but we can clear references
                self._channels.clear()
                self._adc = None
                logging.info("ADS1115 resources cleaned up")
            except Exception as e:
                logging.error(f"Error during cleanup: {e}")