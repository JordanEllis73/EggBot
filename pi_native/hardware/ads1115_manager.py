import time
import threading
from typing import Optional, List, Dict
from dataclasses import dataclass
import logging

# Global variables for library availability
BLINKA_AVAILABLE = False
SMBUS_AVAILABLE = False
board = None
busio = None
ADS = None
AnalogIn = None
smbus2 = None

def _try_import_blinka():
    """Safely try to import Blinka libraries"""
    global BLINKA_AVAILABLE, board, busio, ADS, AnalogIn
    try:
        import board as _board
        import busio as _busio
        import adafruit_ads1x15.ads1115 as _ADS
        from adafruit_ads1x15.analog_in import AnalogIn as _AnalogIn

        # Only assign if all imports succeed
        board = _board
        busio = _busio
        ADS = _ADS
        AnalogIn = _AnalogIn
        BLINKA_AVAILABLE = True
        # Use print as fallback during import time
        print("INFO: Adafruit Blinka libraries imported successfully")

    except ImportError as e:
        BLINKA_AVAILABLE = False
        print(f"WARNING: Adafruit Blinka libraries not available: {e}")
    except Exception as e:
        BLINKA_AVAILABLE = False
        print(f"WARNING: Adafruit Blinka initialization failed: {e}")

def _try_import_smbus():
    """Safely try to import SMBus2 library"""
    global SMBUS_AVAILABLE, smbus2
    try:
        import smbus2 as _smbus2
        smbus2 = _smbus2
        SMBUS_AVAILABLE = True
        # Use print as fallback during import time
        print("INFO: SMBus2 library imported successfully")
    except ImportError as e:
        SMBUS_AVAILABLE = False
        print(f"WARNING: SMBus2 library not available: {e}")

# Try imports on module load
_try_import_blinka()
_try_import_smbus()

HARDWARE_AVAILABLE = BLINKA_AVAILABLE or SMBUS_AVAILABLE

@dataclass
class ProbeReading:
    channel: int
    voltage: float
    raw_value: int
    timestamp: float

class ADS1115Manager:
    """Manages I2C communication with ADS1115 ADC for temperature probe readings"""

    def __init__(self, i2c_address: int = 0x48, simulate: bool = False, force_smbus: bool = False):
        self.i2c_address = i2c_address
        self.simulate = simulate or not HARDWARE_AVAILABLE
        self.force_smbus = force_smbus
        self.use_smbus = False
        self._lock = threading.Lock()
        self._adc = None
        self._smbus = None
        self._channels: Dict[int, AnalogIn] = {}
        self._last_readings: Dict[int, ProbeReading] = {}

        # Import hardware config for proper ADC settings
        try:
            from pi_native.config.hardware import hardware_config
            self.adc_config = hardware_config.adc
        except ImportError:
            # Fallback config if import fails
            from dataclasses import dataclass
            @dataclass
            class FallbackADCConfig:
                sample_rate: int = 860
                gain: int = 1
                supply_voltage: float = 3.3
            self.adc_config = FallbackADCConfig()

        if not self.simulate:
            self._initialize_hardware()

        if self.simulate:
            logging.info(f"ADS1115Manager initialized in SIMULATION mode")
        elif self.use_smbus:
            logging.info(f"ADS1115Manager initialized using SMBus2 library")
        else:
            logging.info(f"ADS1115Manager initialized using Adafruit Blinka library")

        # Also log library availability status
        logging.info(f"Library availability - Blinka: {BLINKA_AVAILABLE}, SMBus2: {SMBUS_AVAILABLE}")
    
    def _initialize_hardware(self) -> None:
        """Initialize I2C connection and ADS1115"""
        if self.force_smbus or not BLINKA_AVAILABLE:
            self._initialize_smbus()
        else:
            self._initialize_blinka()

    def _initialize_blinka(self) -> None:
        """Initialize using Adafruit Blinka libraries"""
        if not BLINKA_AVAILABLE:
            logging.error("Blinka libraries not available")
            if SMBUS_AVAILABLE:
                logging.info("Falling back to SMBus implementation")
                self._initialize_smbus()
            else:
                logging.warning("No I2C libraries available, falling back to simulation mode")
                self.simulate = True
            return

        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            self._adc = ADS.ADS1115(i2c, address=self.i2c_address)

            # Initialize all 4 channels
            for i in range(4):
                channel_pin = getattr(ADS, f'P{i}')
                self._channels[i] = AnalogIn(self._adc, channel_pin)

            logging.info(f"ADS1115 initialized with Blinka on I2C address 0x{self.i2c_address:02x}")
            self.use_smbus = False

        except Exception as e:
            logging.error(f"Failed to initialize ADS1115 with Blinka: {e}")
            if SMBUS_AVAILABLE:
                logging.info("Falling back to SMBus implementation")
                self._initialize_smbus()
            else:
                logging.warning("No I2C libraries available, falling back to simulation mode")
                self.simulate = True

    def _initialize_smbus(self) -> None:
        """Initialize using SMBus2 library"""
        if not SMBUS_AVAILABLE:
            logging.error("SMBus2 not available")
            self.simulate = True
            return

        try:
            self._smbus = smbus2.SMBus(1)  # I2C bus 1 on Raspberry Pi

            # Test connection by reading config register
            config = self._smbus.read_word_data(self.i2c_address, 0x01)
            logging.info(f"ADS1115 initialized with SMBus on I2C address 0x{self.i2c_address:02x} (config: 0x{config:04x})")
            logging.info(f"SMBus ADC config - Sample rate: {self.adc_config.sample_rate} SPS, Gain: {self.adc_config.gain}")
            self.use_smbus = True

        except Exception as e:
            logging.error(f"Failed to initialize ADS1115 with SMBus: {e}")
            self.simulate = True
            logging.warning("Falling back to simulation mode")
    
    def read_channel(self, channel: int) -> Optional[ProbeReading]:
        """Read voltage from specified channel (0-3)"""
        if channel < 0 or channel > 3:
            raise ValueError(f"Invalid channel {channel}. Must be 0-3")

        with self._lock:
            if self.simulate:
                return self._simulate_reading(channel)

            if self.use_smbus:
                return self._read_channel_smbus(channel)
            else:
                return self._read_channel_blinka(channel)

    def _read_channel_blinka(self, channel: int) -> Optional[ProbeReading]:
        """Read channel using Adafruit Blinka"""
        if not BLINKA_AVAILABLE or not self._channels:
            logging.error("Blinka not available or channels not initialized")
            return None

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
            logging.error(f"Error reading channel {channel} with Blinka: {e}")
            return None

    def _read_channel_smbus(self, channel: int) -> Optional[ProbeReading]:
        """Read channel using SMBus2 with proper ADS1115 configuration"""
        try:
            # ADS1115 register addresses
            CONFIG_REG = 0x01
            CONVERSION_REG = 0x00

            # Map sample rates to ADS1115 data rate bits (DR[7:5])
            data_rate_map = {
                8: 0x00,    # 000 = 8 SPS
                16: 0x20,   # 001 = 16 SPS
                32: 0x40,   # 010 = 32 SPS
                64: 0x60,   # 011 = 64 SPS
                128: 0x80,  # 100 = 128 SPS (default)
                250: 0xA0,  # 101 = 250 SPS
                475: 0xC0,  # 110 = 475 SPS
                860: 0xE0   # 111 = 860 SPS
            }

            # Map gain to PGA bits (PGA[11:9])
            gain_map = {
                1: (0x0200, 4.096),  # ±4.096V
                2: (0x0400, 2.048),  # ±2.048V
                4: (0x0600, 1.024),  # ±1.024V
                8: (0x0800, 0.512),  # ±0.512V
                16: (0x0A00, 0.256)  # ±0.256V
            }

            # Get configuration from hardware config
            data_rate_bits = data_rate_map.get(self.adc_config.sample_rate, 0xE0)  # Default to 860 SPS
            gain_bits, voltage_range = gain_map.get(self.adc_config.gain, (0x0200, 4.096))  # Default to ±4.096V

            # Calculate conversion time based on sample rate (add safety margin)
            conversion_time = (1.0 / self.adc_config.sample_rate) + 0.001  # Add 1ms safety margin

            # Build configuration word
            # Bits: OS[15]=1 (start), MUX[14:12]=channel+4 (single-ended), PGA[11:9], MODE[8]=1 (single-shot)
            # DR[7:5], COMP_MODE[4]=0, COMP_POL[3]=0, COMP_LAT[2]=0, COMP_QUE[1:0]=11 (disable comparator)
            config = (
                0x8000 |                    # OS: Start conversion
                ((channel + 4) << 12) |     # MUX: Single-ended input (AIN0-3 = channel+4)
                gain_bits |                 # PGA: Programmable gain
                0x0100 |                    # MODE: Single-shot mode
                data_rate_bits |            # DR: Data rate
                0x0003                      # COMP_QUE: Disable comparator
            )

            # Write configuration (big-endian)
            config_bytes = [(config >> 8) & 0xFF, config & 0xFF]
            self._smbus.write_i2c_block_data(self.i2c_address, CONFIG_REG, config_bytes)

            # Wait for conversion with proper timing
            time.sleep(conversion_time)

            # Poll for conversion completion (optional - check OS bit)
            max_polls = 10
            for _ in range(max_polls):
                config_read = self._smbus.read_i2c_block_data(self.i2c_address, CONFIG_REG, 2)
                config_word = (config_read[0] << 8) | config_read[1]
                if config_word & 0x8000:  # OS bit set = conversion complete
                    break
                time.sleep(0.001)  # Small additional wait

            # Read conversion result (16-bit signed, big-endian)
            data = self._smbus.read_i2c_block_data(self.i2c_address, CONVERSION_REG, 2)
            raw_value = (data[0] << 8) | data[1]

            # Convert to signed 16-bit
            if raw_value > 32767:
                raw_value -= 65536

            # Convert to voltage using correct voltage range
            voltage = (raw_value * voltage_range) / 32767.0

            # Clamp voltage to valid range (prevent negative readings from noise)
            voltage = max(0.0, min(voltage, voltage_range))

            reading = ProbeReading(
                channel=channel,
                voltage=voltage,
                raw_value=raw_value,
                timestamp=time.time()
            )

            self._last_readings[channel] = reading
            return reading

        except Exception as e:
            logging.error(f"Error reading channel {channel} with SMBus: {e}")
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
        if not self.simulate:
            try:
                if self.use_smbus and self._smbus:
                    self._smbus.close()
                    self._smbus = None
                    logging.info("SMBus connection closed")
                elif self._adc:
                    # ADS1115 doesn't require explicit cleanup, but we can clear references
                    self._channels.clear()
                    self._adc = None
                    logging.info("Blinka ADS1115 resources cleaned up")
            except Exception as e:
                logging.error(f"Error during cleanup: {e}")