import threading
import time
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.meater_probe import MeaterProbe
from app.bluetooth_scanner import bluetooth_scanner


class MeaterManager:
    def __init__(self):
        self.probe: Optional[MeaterProbe] = None
        self.is_connected = False
        self.is_connecting = False
        self.is_scanning = False
        self.last_data: Optional[Dict[str, Any]] = None
        self.last_update: Optional[datetime] = None
        self.connection_thread: Optional[threading.Thread] = None
        self.update_thread: Optional[threading.Thread] = None
        self.scan_thread: Optional[threading.Thread] = None
        self.should_stop = False
        self.address: Optional[str] = None

    def connect(self, address: str) -> bool:
        """Start connection to Meater probe in background thread"""
        if self.is_connected or self.is_connecting:
            return False
            
        self.address = address
        self.is_connecting = True
        self.should_stop = False
        
        self.connection_thread = threading.Thread(target=self._connect_worker)
        self.connection_thread.daemon = True
        self.connection_thread.start()
        
        return True

    def _connect_worker(self):
        """Worker thread for connecting to probe"""
        try:
            self.probe = MeaterProbe(self.address)
            self.is_connected = True
            self.is_connecting = False
            
            # Start update thread
            self.update_thread = threading.Thread(target=self._update_worker)
            self.update_thread.daemon = True
            self.update_thread.start()
            
        except Exception as e:
            print(f"Failed to connect to Meater probe: {e}")
            self.is_connected = False
            self.is_connecting = False
            self.probe = None

    def _update_worker(self):
        """Worker thread for updating probe data"""
        while self.is_connected and not self.should_stop:
            try:
                if self.probe:
                    self.probe.update()
                    self.last_data = {
                        'probe_temp_c': self.probe.get_tip_c(),
                        'probe_temp_f': self.probe.get_tip_f(),
                        'ambient_temp_c': self.probe.get_ambient_c(),
                        'ambient_temp_f': self.probe.get_ambient_f(),
                        'battery_percent': self.probe.get_battery(),
                        'address': self.probe.get_address(),
                        'firmware': self.probe.get_firmware(),
                        'id': self.probe.get_id()
                    }
                    self.last_update = datetime.utcnow()
                    
                time.sleep(1)  # Update every second
                
            except Exception as e:
                print(f"Error updating Meater probe data: {e}")
                self.disconnect()
                break

    def disconnect(self):
        """Disconnect from probe and stop all threads"""
        self.should_stop = True
        self.is_connected = False
        self.is_connecting = False
        
        if self.probe:
            try:
                self.probe.disconnect()
            except:
                pass
            self.probe = None
            
        self.last_data = None
        self.last_update = None

    def get_status(self) -> Dict[str, Any]:
        """Get current probe status"""
        return {
            'is_connected': self.is_connected,
            'is_connecting': self.is_connecting,
            'is_scanning': self.is_scanning,
            'address': self.address,
            'last_update': self.last_update.isoformat() + 'Z' if self.last_update else None,
            'data': self.last_data
        }

    def get_data(self) -> Optional[Dict[str, Any]]:
        """Get latest probe data"""
        return self.last_data

    def scan_for_devices(self) -> List[str]:
        """Scan for available Meater devices and return their addresses"""
        try:
            return bluetooth_scanner.scan_for_meater_devices(scan_time=5.0)
        except Exception as e:
            print(f"Error scanning for devices: {e}")
            return []

    def scan_and_connect(self) -> bool:
        """Scan for Meater devices and connect to the first one found"""
        if self.is_connected or self.is_connecting or self.is_scanning:
            return False
            
        self.is_scanning = True
        self.scan_thread = threading.Thread(target=self._scan_and_connect_worker)
        self.scan_thread.daemon = True
        self.scan_thread.start()
        
        return True

    def _scan_and_connect_worker(self):
        """Worker thread for scanning and connecting"""
        try:
            print("Scanning for Meater devices...")
            devices = self.scan_for_devices()
            
            if devices:
                print(f"Found {len(devices)} Meater device(s): {devices}")
                # Connect to the first device found
                first_device = devices[0]
                print(f"Attempting to connect to {first_device}")
                
                self.is_scanning = False
                self.connect(first_device)
            else:
                print("No Meater devices found")
                self.is_scanning = False
                
        except Exception as e:
            print(f"Error in scan and connect worker: {e}")
            self.is_scanning = False

    def stop_scan(self):
        """Stop any ongoing scan"""
        self.is_scanning = False


# Global instance
meater_manager = MeaterManager()