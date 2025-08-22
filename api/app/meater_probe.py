import time
from typing import Optional

try:
    import bluepy3.btle as btle
    BLUETOOTH_AVAILABLE = True
except ImportError:
    print("Warning: bluepy3 not available - Meater functionality disabled")
    BLUETOOTH_AVAILABLE = False
    btle = None


class MeaterProbe:
    """
    Meater Bluetooth probe interface
    """
    
    def __init__(self, addr: str):
        if not BLUETOOTH_AVAILABLE:
            raise ImportError("Bluetooth functionality not available - bluepy3 not installed")
            
        self._addr = addr
        self._dev: Optional[btle.Peripheral] = None
        self._tip: float = 0.0
        self._ambient: float = 0.0
        self._battery: int = 0
        self._firmware: str = ""
        self._id: str = ""
        self._lastUpdate: float = 0.0
        self.connect()

    @staticmethod
    def bytes_to_int(byte0: int, byte1: int) -> int:
        """Convert two bytes to integer"""
        return byte1 * 256 + byte0

    @staticmethod
    def convert_ambient(array: bytearray) -> int:
        """Convert temperature array to ambient temperature"""
        tip = MeaterProbe.bytes_to_int(array[0], array[1])
        ra = MeaterProbe.bytes_to_int(array[2], array[3])
        oa = MeaterProbe.bytes_to_int(array[4], array[5])
        return int(tip + (max(0, ((((ra - min(48, oa)) * 16) * 589)) / 1487)))

    @staticmethod
    def to_celsius(value: float) -> float:
        """Convert raw value to Celsius"""
        return (float(value) + 8.0) / 16.0

    @staticmethod
    def to_fahrenheit(value: float) -> float:
        """Convert raw value to Fahrenheit"""
        return ((MeaterProbe.to_celsius(value) * 9) / 5) + 32.0

    def get_tip(self) -> float:
        """Get raw tip temperature"""
        return self._tip

    def get_tip_f(self) -> float:
        """Get tip temperature in Fahrenheit"""
        return MeaterProbe.to_fahrenheit(self._tip)

    def get_tip_c(self) -> float:
        """Get tip temperature in Celsius"""
        return MeaterProbe.to_celsius(self._tip)

    def get_ambient_f(self) -> float:
        """Get ambient temperature in Fahrenheit"""
        return MeaterProbe.to_fahrenheit(self._ambient)

    def get_ambient(self) -> float:
        """Get raw ambient temperature"""
        return self._ambient

    def get_ambient_c(self) -> float:
        """Get ambient temperature in Celsius"""
        return MeaterProbe.to_celsius(self._ambient)

    def get_battery(self) -> int:
        """Get battery percentage"""
        return self._battery

    def get_address(self) -> str:
        """Get Bluetooth address"""
        return self._addr

    def get_id(self) -> str:
        """Get probe ID"""
        return self._id

    def get_firmware(self) -> str:
        """Get firmware version"""
        return self._firmware

    def connect(self):
        """Connect to the probe via Bluetooth"""
        if not BLUETOOTH_AVAILABLE:
            raise ImportError("Bluetooth functionality not available")
        self._dev = btle.Peripheral(self._addr)

    def disconnect(self):
        """Disconnect from the probe"""
        if self._dev:
            try:
                self._dev.disconnect()
            except:
                pass
            self._dev = None

    def read_characteristic(self, characteristic_id: int) -> bytearray:
        """Read a characteristic from the probe"""
        if not self._dev:
            raise ConnectionError("Not connected to probe")
        return bytearray(self._dev.readCharacteristic(characteristic_id))

    def update(self):
        """Update probe readings"""
        if not self._dev:
            raise ConnectionError("Not connected to probe")
            
        try:
            temp_bytes = self.read_characteristic(31)
            battery_bytes = self.read_characteristic(35)
            
            self._tip = MeaterProbe.bytes_to_int(temp_bytes[0], temp_bytes[1])
            self._ambient = MeaterProbe.convert_ambient(temp_bytes)
            self._battery = MeaterProbe.bytes_to_int(battery_bytes[0], battery_bytes[1]) * 10
            
            firmware_id_str = str(self.read_characteristic(22))
            if "_" in firmware_id_str:
                self._firmware, self._id = firmware_id_str.split("_", 1)
            else:
                self._firmware = firmware_id_str
                self._id = "unknown"
                
            self._lastUpdate = time.time()
            
        except Exception as e:
            print(f"Error updating probe data: {e}")
            raise

    def __str__(self) -> str:
        return (f"{self.get_address()} {self.get_firmware()} probe: {self.get_id()} "
                f"tip: {self.get_tip_f():.1f}°F/{self.get_tip_c():.1f}°C "
                f"ambient: {self.get_ambient_f():.1f}°F/{self.get_ambient_c():.1f}°C "
                f"battery: {self.get_battery()}% "
                f"age: {time.time() - self._lastUpdate:.0f}s")