import time
from typing import List, Dict, Any

try:
    import bluepy3.btle as btle
    BLUETOOTH_AVAILABLE = True
except ImportError:
    print("Warning: bluepy3 not available - Bluetooth scanning disabled")
    BLUETOOTH_AVAILABLE = False
    btle = None


class BluetoothScanner:
    """
    Bluetooth Low Energy device scanner for finding Meater probes
    """
    
    def __init__(self):
        self.scanner = None
        
    def scan_for_meater_devices(self, scan_time: float = 5.0) -> List[str]:
        """
        Scan for Meater devices and return their MAC addresses
        
        Args:
            scan_time: How long to scan in seconds
            
        Returns:
            List of MAC addresses for discovered Meater devices
        """
        if not BLUETOOTH_AVAILABLE:
            print("Bluetooth not available - cannot scan for devices")
            return []
            
        try:
            # Create scanner
            self.scanner = btle.Scanner()
            
            print(f"Scanning for Meater devices for {scan_time} seconds...")
            
            # Scan for devices
            devices = self.scanner.scan(scan_time)
            
            meater_devices = []
            
            for device in devices:
                # Check if device name contains "MEATER"
                device_name = ""
                
                # Look through scan data for device name
                for (adtype, description, value) in device.getScanData():
                    if adtype == 8 or adtype == 9:  # Short Local Name or Complete Local Name
                        device_name = value
                        break
                
                # Check if this is a Meater device
                if "meater" in device_name.lower():
                    print(f"Found Meater device: {device.addr} ({device_name})")
                    meater_devices.append(device.addr.upper())
                    
            if not meater_devices:
                print("No Meater devices found")
                
            return meater_devices
            
        except Exception as e:
            print(f"Error scanning for devices: {e}")
            return []
        finally:
            if self.scanner:
                try:
                    # Stop scanning
                    self.scanner.stop()
                except:
                    pass
                self.scanner = None
    
    def get_device_info(self, address: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific device
        
        Args:
            address: MAC address of the device
            
        Returns:
            Dictionary with device information
        """
        if not BLUETOOTH_AVAILABLE:
            return {}
            
        try:
            self.scanner = btle.Scanner()
            devices = self.scanner.scan(3.0)  # Short scan
            
            for device in devices:
                if device.addr.upper() == address.upper():
                    info = {
                        'address': device.addr.upper(),
                        'rssi': device.rssi,
                        'connectable': device.connectable,
                        'scan_data': {}
                    }
                    
                    # Extract scan data
                    for (adtype, description, value) in device.getScanData():
                        info['scan_data'][description] = value
                        
                    return info
                    
            return {}
            
        except Exception as e:
            print(f"Error getting device info: {e}")
            return {}
        finally:
            if self.scanner:
                try:
                    self.scanner.stop()
                except:
                    pass
                self.scanner = None


# Global scanner instance
bluetooth_scanner = BluetoothScanner()