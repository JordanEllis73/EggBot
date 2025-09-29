"""
Pi-native ControllerIO replacement
Drop-in replacement for serial_io.ControllerIO using Pi-native hardware control
"""

import threading
from datetime import datetime
from typing import Optional, List
import logging

from pi_native.control.eggbot_controller import EggBotController
from pi_native.config.pid import default_control_config, PID_PRESETS
from app.config import settings

class PiNativeControllerIO:
    """Pi-native controller that maintains API compatibility with original ControllerIO"""
    
    def __init__(self) -> None:
        self._lock = threading.Lock()
        
        # Initialize Pi-native controller
        simulate = settings.simulate
        self.controller = EggBotController(
            control_config=default_control_config,
            simulate=simulate
        )
        
        # Start the controller
        self.controller.start()
        
        # Legacy compatibility tracking
        self._setpoint_history = [(110.0, "INIT", 0)]
        
        logging.info(f"[PI_CONTROLLER {id(self)}] INIT: Pi-native controller started")
    
    def set_setpoint(self, c: float) -> None:
        """Set pit temperature setpoint"""
        with self._lock:
            logging.info(f"[PI_CONTROLLER {id(self)}] setting setpoint to {c} C")
            self._setpoint_history.append((c, "API_SET", 0))
            if len(self._setpoint_history) > 10:
                self._setpoint_history = self._setpoint_history[-10:]
        
        self.controller.set_setpoint(c)
    
    def get_setpoint(self) -> float:
        """Get current pit temperature setpoint"""
        return self.controller.get_setpoint()
    
    def set_meat_setpoint(self, c: float) -> None:
        """Set meat temperature setpoint"""
        with self._lock:
            logging.info(f"setting meat setpoint to {c} C")
        self.controller.set_meat_setpoint(c)
    
    def get_meat_setpoint(self) -> Optional[float]:
        """Get current meat temperature setpoint"""
        return self.controller.get_meat_setpoint()
    
    def set_damper(self, percent: int) -> None:
        """Set damper position (switches to manual mode)"""
        percent = max(0, min(100, int(percent)))
        self.controller.set_damper_percent(float(percent))
    
    def set_pid_gains(self, kp: float, ki: float, kd: float) -> None:
        """Set PID controller gains"""
        self.controller.set_pid_gains(kp, ki, kd)
    
    def set_control_mode(self, mode: str) -> None:
        """Set control mode: 'manual' or 'automatic'"""
        if mode not in ["manual", "automatic"]:
            raise ValueError(f"Invalid control mode: {mode}. Use 'manual' or 'automatic'")
        
        self.controller.set_control_mode(mode)
    
    def get_control_mode(self) -> str:
        """Get current control mode"""
        return self.controller.get_control_mode()

    def get_temperature_limits(self) -> dict:
        """Get current temperature limits from configuration"""
        return self.controller.get_temperature_limits()

    def get_status(self) -> dict:
        """Get current controller status (legacy compatible format)"""
        status = self.controller.get_status()
        
        # Convert to legacy format while maintaining new fields
        legacy_status = {
            "pit_temp_c": status.get("pit_temp_c"),
            "meat_temp_c": status.get("meat_temp_1_c"),  # Legacy compatibility
            "meat_temp_1_c": status.get("meat_temp_1_c"),  # New field
            "meat_temp_2_c": status.get("meat_temp_2_c"),  # New field  
            "ambient_temp_c": status.get("ambient_temp_c"),  # New field
            "damper_percent": int(status.get("damper_percent", 0)),
            "setpoint_c": status.get("setpoint_c"),
            "meat_setpoint_c": status.get("meat_setpoint_c"),
            "control_mode": status.get("control_mode", "manual"),
            "safety_shutdown": status.get("safety_shutdown", False),  # New field
            "connected_probes": status.get("connected_probes", []),  # New field
            "pid_output": status.get("pid_output", 0.0),  # New field
            "pid_error": status.get("pid_error", 0.0),  # New field
            "timestamp": datetime.now().isoformat() + "Z",
        }
        
        # Debug logging for legacy compatibility
        recent_changes = [f"{val}@{source}" for val, source, ts in self._setpoint_history[-3:]]
        logging.info(f"[PI_CONTROLLER {id(self)}] get_status call: setpoint={legacy_status['setpoint_c']}")
        logging.debug(f"[PI_CONTROLLER {id(self)}] recent setpoint history: {recent_changes}")
        
        return legacy_status
    
    def get_telemetry(self) -> List[dict]:
        """Get telemetry data (legacy compatible format)"""
        telemetry_data = self.controller.get_telemetry()
        
        # Convert to legacy format
        legacy_telemetry = []
        for point in telemetry_data:
            legacy_point = {
                "pit_temp_c": point.get("pit_temp_c"),
                "meat_temp_c": point.get("meat_temp_1_c"),  # Legacy compatibility
                "damper_percent": int(point.get("damper_percent", 0)),
                "setpoint_c": point.get("setpoint_c"),
                "meat_setpoint_c": point.get("meat_setpoint_c"),
                "timestamp": point.get("timestamp"),
            }
            legacy_telemetry.append(legacy_point)
        
        return legacy_telemetry
    
    # Pi-native specific methods (new functionality)
    def get_enhanced_status(self) -> dict:
        """Get full Pi-native status with all temperature probes"""
        return self.controller.get_status()
    
    def get_enhanced_telemetry(self) -> List[dict]:
        """Get full Pi-native telemetry data"""
        return self.controller.get_telemetry()
    
    def get_probe_status(self) -> dict:
        """Get status of all temperature probes"""
        return self.controller.get_probe_status()
    
    def get_system_status(self) -> dict:
        """Get overall system status"""
        probe_status = self.controller.get_probe_status()
        performance = self.controller.get_performance_stats()
        
        return {
            "probes": probe_status,
            "system_enabled": self.controller.is_running(),
            "safety_shutdown": self.controller.get_status().get("safety_shutdown", False),
            "control_loop_count": performance.get("control_loop_count", 0),
            "telemetry_points": performance.get("telemetry_points", 0),
            "connected_probes": performance.get("connected_probes", 0)
        }
    
    def load_pid_preset(self, preset_name: str) -> None:
        """Load a PID tuning preset"""
        self.controller.load_pid_preset(preset_name)
    
    def get_available_presets(self) -> List[str]:
        """Get list of available PID presets"""
        return self.controller.get_available_presets()
    
    def get_pid_tuning_info(self) -> dict:
        """Get PID tuning information"""
        return self.controller.get_pid_tuning_info()
    
    def calibrate_probe(self, probe_name: str, actual_temperature: float) -> None:
        """Calibrate a temperature probe"""
        self.controller.calibrate_probe(probe_name, actual_temperature)
    
    def get_performance_stats(self) -> dict:
        """Get controller performance statistics"""
        return self.controller.get_performance_stats()
    
    def reset_safety_shutdown(self) -> None:
        """Reset safety shutdown after resolving issues"""
        self.controller.reset_safety_shutdown()
    
    def clear_telemetry(self) -> None:
        """Clear telemetry data"""
        self.controller.clear_telemetry()
    
    def start_csv_logging(self, filename: str, interval_seconds: float = 5.0) -> None:
        """Start CSV logging"""
        self.controller.start_csv_logging(filename, interval_seconds)

    def stop_csv_logging(self) -> str:
        """Stop CSV logging and return file path"""
        return self.controller.stop_csv_logging()

    def get_csv_logging_status(self) -> dict:
        """Get CSV logging status"""
        return self.controller.get_csv_logging_status()

    def close(self) -> None:
        """Clean shutdown of the controller"""
        if hasattr(self, 'controller'):
            self.controller.stop()
        logging.info(f"[PI_CONTROLLER {id(self)}] closed")
    
    def __del__(self):
        """Ensure clean shutdown on deletion"""
        try:
            self.close()
        except Exception:
            pass