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
        
        # Try primary scanning method
        devices = self._scan_primary(scan_time)
        if devices:
            return devices
            
        # If primary fails, try alternative method
        print("Primary scan failed, trying alternative approach...")
        return self._scan_alternative(scan_time)
    
    def _scan_primary(self, scan_time: float) -> List[str]:
        """Primary scanning method using bluepy3 Scanner"""
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
                print("No Meater devices found with primary scan")
                
            return meater_devices
            
        except Exception as e:
            print(f"Error in primary scan: {e}")
            return []
        finally:
            if self.scanner:
                try:
                    self.scanner.stop()
                except:
                    pass
                self.scanner = None
    
    def _scan_alternative(self, scan_time: float) -> List[str]:
        """Alternative scanning method without requiring BLE management"""
        try:
            import subprocess
            import re
            
            print("Using alternative Bluetooth scanning via hcitool...")
            
            # Use hcitool lescan for BLE devices
            cmd = ["timeout", str(int(scan_time)), "hcitool", "lescan"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=scan_time + 2)
            
            meater_devices = []
            
            # Parse output for Meater devices
            for line in result.stdout.split('\n'):
                if 'meater' in line.lower():
                    # Extract MAC address from line like "AA:BB:CC:DD:EE:FF MEATER"
                    mac_match = re.search(r'([0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2})', line)
                    if mac_match:
                        mac_addr = mac_match.group(1).upper()
                        print(f"Found Meater device (alternative): {mac_addr}")
                        meater_devices.append(mac_addr)
            
            if not meater_devices:
                print("No Meater devices found with alternative scan")
                
            return meater_devices
            
        except Exception as e:
            print(f"Error in alternative scan: {e}")
            return []
    
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