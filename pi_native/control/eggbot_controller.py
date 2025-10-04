import time
import threading
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import csv
import os
from pathlib import Path

from pi_native.control.pid_controller import PIDController, PIDState
from pi_native.control.temperature_monitor import TemperatureMonitor, TemperatureReading
from pi_native.hardware.servo_controller import ServoController
from pi_native.config.pid import PIDConfig, default_control_config, PID_PRESETS
from pi_native.config.hardware import hardware_config

@dataclass
class ControllerState:
    """Current state of the EggBot controller"""
    # Temperatures
    pit_temp_c: Optional[float] = None
    meat_temp_1_c: Optional[float] = None
    meat_temp_2_c: Optional[float] = None
    ambient_temp_c: Optional[float] = None
    
    # Control parameters
    setpoint_c: float = 110.0
    meat_setpoint_c: Optional[float] = None
    damper_percent: float = 0.0
    
    # Control mode
    control_mode: str = "manual"  # "manual" or "automatic"
    
    # PID state
    pid_output: float = 0.0
    pid_error: float = 0.0
    pid_gains: tuple = (2.0, 0.1, 1.0)
    
    # System status
    system_enabled: bool = True
    safety_shutdown: bool = False
    connected_probes: List[str] = None
    
    # Timestamps
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.connected_probes is None:
            self.connected_probes = []

class EggBotController:
    """Main controller that orchestrates all EggBot components"""
    
    def __init__(self, 
                 control_config: Optional[PIDConfig] = None,
                 simulate: bool = False):
        
        self.simulate = simulate
        self.control_config = control_config or default_control_config
        
        # Initialize components
        self.temperature_monitor = TemperatureMonitor(
            update_interval=self.control_config.main_loop_interval,
            safety_limits=self.control_config.safety,
            simulate=simulate
        )
        
        self.pid_controller = PIDController(self.control_config.pid)
        
        self.servo_controller = ServoController(
            gpio_pin=hardware_config.gpio.servo_pin,
            simulate=simulate,
            config=hardware_config.servo,
            pigpio_host="pigpiod",  # Use Docker service name
            pigpio_port=8888
        )
        
        # Controller state
        self.state = ControllerState()
        self._lock = threading.Lock()
        
        # Control loop threading
        self._running = False
        self._control_thread: Optional[threading.Thread] = None
        
        # Telemetry data storage
        self.telemetry_data: List[Dict[str, Any]] = []
        self.max_telemetry_points = 7200  # ~2 hours at 1 second intervals
        
        # Performance tracking
        self.control_loop_count = 0
        self.last_control_time = 0.0

        # CSV logging
        self.csv_logging_enabled = False
        self.csv_file_path: Optional[str] = None
        self.csv_writer: Optional[csv.DictWriter] = None
        self.csv_file_handle: Optional[object] = None
        self.csv_start_time: Optional[float] = None
        self.csv_logging_interval = 5.0  # Default 5 seconds
        self.csv_last_log_time = 0.0

        # Setup temperature monitor alerts
        self.temperature_monitor.add_alert_callback(self._handle_temperature_alert)
        
        # Initialize setpoint
        self.pid_controller.set_setpoint(self.state.setpoint_c)
        
        logging.info(f"EggBotController initialized (simulate={simulate})")
    
    def _handle_temperature_alert(self, level: str, message: str) -> None:
        """Handle temperature alerts from the monitor"""
        if level == "CRITICAL":
            logging.error(f"CRITICAL ALERT: {message}")
            self._emergency_shutdown()
        else:
            logging.warning(f"Temperature Alert [{level}]: {message}")
    
    def _emergency_shutdown(self) -> None:
        """Emergency shutdown procedure"""
        logging.error("EMERGENCY SHUTDOWN TRIGGERED")
        
        with self._lock:
            self.state.safety_shutdown = True
            self.state.control_mode = "manual"
        
        # Close damper immediately
        self.servo_controller.set_position_percent(0)
        
        # Disable PID controller
        self.pid_controller.disable()
    
    def start(self) -> None:
        """Start the controller"""
        if self._running:
            return
        
        # Start temperature monitoring
        self.temperature_monitor.start_monitoring()
        
        # Start control loop
        self._running = True
        self._control_thread = threading.Thread(target=self._control_loop, daemon=True)
        self._control_thread.start()
        
        logging.info("EggBotController started")
    
    def stop(self) -> None:
        """Stop the controller"""
        self._running = False
        
        if self._control_thread and self._control_thread.is_alive():
            self._control_thread.join(timeout=3.0)
        
        # Stop temperature monitoring
        self.temperature_monitor.stop_monitoring()

        # Stop CSV logging if active
        if self.csv_logging_enabled:
            try:
                self.stop_csv_logging()
            except Exception as e:
                logging.error(f"Error stopping CSV logging: {e}")

        # Close damper and stop servo
        self.servo_controller.set_position_percent(0)
        time.sleep(0.5)
        self.servo_controller.close()

        logging.info("EggBotController stopped")
    
    def _control_loop(self) -> None:
        """Main control loop"""
        last_control_time = 0.0
        last_telemetry_time = 0.0
        
        while self._running:
            try:
                current_time = time.time()
                
                # Update temperatures
                self._update_temperatures()
                
                # Run PID control at specified interval
                if (current_time - last_control_time) >= self.control_config.control_loop_interval:
                    self._run_pid_control()
                    last_control_time = current_time
                    self.control_loop_count += 1
                
                # Log telemetry at specified interval
                if (current_time - last_telemetry_time) >= self.control_config.telemetry_interval:
                    self._log_telemetry()
                    last_telemetry_time = current_time

                # Log CSV data at specified interval
                if (self.csv_logging_enabled and
                    (current_time - self.csv_last_log_time) >= self.csv_logging_interval):
                    self._log_csv_data()
                    self.csv_last_log_time = current_time

                # Sleep until next cycle
                time.sleep(self.control_config.main_loop_interval)
                
            except Exception as e:
                logging.error(f"Error in control loop: {e}")
                time.sleep(1.0)
    
    def _update_temperatures(self) -> None:
        """Update temperature readings from monitor"""
        temps = self.temperature_monitor.get_current_temperatures()
        connected = []
        
        with self._lock:
            self.state.pit_temp_c = temps.get("pit_probe")
            self.state.meat_temp_1_c = temps.get("meat_probe_1") 
            self.state.meat_temp_2_c = temps.get("meat_probe_2")
            self.state.ambient_temp_c = temps.get("ambient_probe")
            
            # Update connected probes list
            for probe_name, temp in temps.items():
                if temp is not None:
                    connected.append(probe_name)
            
            self.state.connected_probes = connected
            self.state.safety_shutdown = self.temperature_monitor.is_safety_shutdown()
    
    def _run_pid_control(self) -> None:
        """Run PID control calculation"""
        with self._lock:
            if (self.state.control_mode != "automatic" or 
                self.state.safety_shutdown or
                self.state.pit_temp_c is None):
                return
            
            # Run PID calculation
            pid_output = self.pid_controller.compute(self.state.pit_temp_c)
            
            # Update servo position
            self.servo_controller.set_position_percent(pid_output)
            
            # Update state
            pid_state = self.pid_controller.get_state()
            self.state.pid_output = pid_output
            self.state.pid_error = pid_state.error
            self.state.damper_percent = self.servo_controller.get_position_percent()
    
    def _log_telemetry(self) -> None:
        """Log telemetry data point"""
        with self._lock:
            # Create telemetry data point
            data_point = {
                "timestamp": datetime.now().isoformat() + "Z",
                "pit_temp_c": self.state.pit_temp_c,
                "meat_temp_1_c": self.state.meat_temp_1_c,
                "meat_temp_2_c": self.state.meat_temp_2_c,
                "ambient_temp_c": self.state.ambient_temp_c,
                "setpoint_c": self.state.setpoint_c,
                "meat_setpoint_c": self.state.meat_setpoint_c,
                "damper_percent": self.state.damper_percent,
                "pid_output": self.state.pid_output,
                "pid_error": self.state.pid_error,
                "control_mode": self.state.control_mode,
                "safety_shutdown": self.state.safety_shutdown
            }
            
            self.telemetry_data.append(data_point)
            
            # Limit telemetry data size
            if len(self.telemetry_data) > self.max_telemetry_points:
                self.telemetry_data = self.telemetry_data[-self.max_telemetry_points:]
    
    def get_status(self) -> Dict[str, Any]:
        """Get current controller status"""
        with self._lock:
            state_dict = asdict(self.state)
            state_dict["timestamp"] = datetime.now().isoformat() + "Z"
            return state_dict
    
    def set_setpoint(self, setpoint_c: float) -> None:
        """Set pit temperature setpoint"""
        # Use configurable safety limits
        min_temp = self.control_config.safety.min_pit_temp
        max_temp = self.control_config.safety.max_pit_temp

        if not (min_temp <= setpoint_c <= max_temp):
            error_msg = f"Setpoint {setpoint_c}°C out of range [{min_temp}-{max_temp}]°C"
            logging.warning(f"Invalid setpoint request: {error_msg}")
            raise ValueError(error_msg)

        with self._lock:
            self.state.setpoint_c = setpoint_c

        self.pid_controller.set_setpoint(setpoint_c)
        logging.info(f"Setpoint set to {setpoint_c}°C (range: [{min_temp}-{max_temp}]°C)")
    
    def get_setpoint(self) -> float:
        """Get current pit temperature setpoint"""
        with self._lock:
            return self.state.setpoint_c
    
    def set_meat_setpoint(self, setpoint_c: Optional[float]) -> None:
        """Set meat temperature setpoint"""
        if setpoint_c is not None:
            # Use configurable safety limits
            min_temp = self.control_config.safety.min_meat_temp
            max_temp = self.control_config.safety.max_meat_temp

            if not (min_temp <= setpoint_c <= max_temp):
                error_msg = f"Meat setpoint {setpoint_c}°C out of range [{min_temp}-{max_temp}]°C"
                logging.warning(f"Invalid meat setpoint request: {error_msg}")
                raise ValueError(error_msg)

        with self._lock:
            self.state.meat_setpoint_c = setpoint_c

        if setpoint_c is not None:
            min_temp = self.control_config.safety.min_meat_temp
            max_temp = self.control_config.safety.max_meat_temp
            logging.info(f"Meat setpoint set to {setpoint_c}°C (range: [{min_temp}-{max_temp}]°C)")
        else:
            logging.info("Meat setpoint cleared (set to None)")
    
    def get_meat_setpoint(self) -> Optional[float]:
        """Get current meat temperature setpoint"""
        with self._lock:
            return self.state.meat_setpoint_c

    def get_temperature_limits(self) -> Dict[str, Dict[str, float]]:
        """Get current temperature limits from configuration"""
        return {
            "pit_temp": {
                "min": self.control_config.safety.min_pit_temp,
                "max": self.control_config.safety.max_pit_temp
            },
            "meat_temp": {
                "min": self.control_config.safety.min_meat_temp,
                "max": self.control_config.safety.max_meat_temp
            }
        }

    def get_servo_diagnostics(self) -> Dict[str, Any]:
        """Get servo diagnostics information"""
        return self.servo_controller.get_servo_diagnostics()

    def test_servo_connectivity(self) -> Dict[str, Any]:
        """Test servo connectivity and return results"""
        return self.servo_controller.test_servo_connectivity()

    def test_servo_movement(self) -> Dict[str, Any]:
        """Test servo movement functionality"""
        try:
            initial_position = self.servo_controller.get_position_percent()

            # Test sequence: move to different positions
            test_positions = [25, 75, 50]
            results = []

            for position in test_positions:
                start_time = time.time()
                self.servo_controller.set_position_percent(position)

                # Wait for movement to complete
                timeout = 10.0  # 10 second timeout
                while (time.time() - start_time < timeout and
                       not self.servo_controller.is_at_target()):
                    time.sleep(0.1)

                actual_position = self.servo_controller.get_position_percent()
                move_time = time.time() - start_time

                results.append({
                    "target_position": position,
                    "actual_position": actual_position,
                    "move_time_seconds": move_time,
                    "position_error": abs(position - actual_position),
                    "timeout": move_time >= timeout
                })

            # Return to initial position
            self.servo_controller.set_position_percent(initial_position)

            return {
                "success": True,
                "test_results": results,
                "initial_position": initial_position
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def set_damper_percent(self, percent: float) -> None:
        """Set damper position manually (switches to manual mode)"""
        percent = max(0, min(100, percent))
        
        with self._lock:
            self.state.control_mode = "manual"
            self.state.damper_percent = percent
        
        self.servo_controller.set_position_percent(percent)
        self.pid_controller.set_auto_mode(False)
        
        logging.info(f"Manual damper set to {percent}%")
    
    def set_control_mode(self, mode: str) -> None:
        """Set control mode: 'manual' or 'automatic'"""
        if mode not in ["manual", "automatic"]:
            raise ValueError(f"Invalid control mode: {mode}")
        
        with self._lock:
            if self.state.safety_shutdown and mode == "automatic":
                raise ValueError("Cannot switch to automatic mode during safety shutdown")
            
            self.state.control_mode = mode
        
        if mode == "automatic":
            self.pid_controller.set_auto_mode(True)
            self.pid_controller.enable()
        else:
            self.pid_controller.set_auto_mode(False)
        
        logging.info(f"Control mode set to {mode}")
    
    def get_control_mode(self) -> str:
        """Get current control mode"""
        with self._lock:
            return self.state.control_mode
    
    def set_pid_gains(self, kp: float, ki: float, kd: float) -> None:
        """Set PID controller gains"""
        self.pid_controller.set_gains(kp, ki, kd)
        
        with self._lock:
            self.state.pid_gains = (kp, ki, kd)
        
        logging.info(f"PID gains set to Kp={kp}, Ki={ki}, Kd={kd}")
    
    def get_pid_gains(self) -> tuple:
        """Get current PID gains"""
        return self.pid_controller.get_gains()
    
    def load_pid_preset(self, preset_name: str) -> None:
        """Load a PID preset configuration"""
        if preset_name not in PID_PRESETS:
            raise ValueError(f"Unknown PID preset: {preset_name}")
        
        preset = PID_PRESETS[preset_name]
        self.set_pid_gains(preset.gains.kp, preset.gains.ki, preset.gains.kd)
        
        logging.info(f"Loaded PID preset: {preset_name}")
    
    def get_available_presets(self) -> List[str]:
        """Get list of available PID presets"""
        return list(PID_PRESETS.keys())
    
    def calibrate_probe(self, probe_name: str, actual_temperature: float) -> None:
        """Calibrate a temperature probe"""
        self.temperature_monitor.calibrate_probe(probe_name, actual_temperature)
    
    def get_probe_status(self) -> Dict[str, Any]:
        """Get status of all temperature probes"""
        probe_status = {}
        all_probes = self.temperature_monitor.get_all_probe_status()
        
        for probe_name, status in all_probes.items():
            probe_status[probe_name] = {
                "connected": status.is_connected,
                "last_temp": status.last_reading.temperature_c if status.last_reading else None,
                "last_update": status.last_update.isoformat() if status.last_update else None,
                "total_readings": status.total_readings,
                "consecutive_errors": status.consecutive_errors,
                "min_temp": status.min_temp if status.min_temp != float('inf') else None,
                "max_temp": status.max_temp if status.max_temp != float('-inf') else None,
                "average_temp": status.average_temp if status.total_readings > 0 else None
            }
        
        return probe_status
    
    def get_telemetry(self) -> List[Dict[str, Any]]:
        """Get telemetry data"""
        with self._lock:
            return self.telemetry_data.copy()
    
    def clear_telemetry(self) -> None:
        """Clear telemetry data"""
        with self._lock:
            self.telemetry_data.clear()
        
        logging.info("Telemetry data cleared")
    
    def get_pid_tuning_info(self) -> Dict[str, Any]:
        """Get PID tuning information"""
        return self.pid_controller.get_tuning_info()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get controller performance statistics"""
        pid_stats = self.pid_controller.get_performance_stats()
        
        return {
            "pid_controller": pid_stats,
            "control_loop_count": self.control_loop_count,
            "telemetry_points": len(self.telemetry_data),
            "connected_probes": len(self.state.connected_probes),
            "uptime_seconds": time.time() - self.last_control_time if self.last_control_time else 0
        }
    
    def reset_safety_shutdown(self) -> None:
        """Reset safety shutdown (after resolving the issue)"""
        self.temperature_monitor.reset_safety_shutdown()
        
        with self._lock:
            self.state.safety_shutdown = False
        
        logging.info("Safety shutdown reset")
    
    def is_running(self) -> bool:
        """Check if controller is running"""
        return self._running

    def start_csv_logging(self, filename: str, interval_seconds: float = 5.0) -> None:
        """Start logging telemetry data to CSV file"""
        if self.csv_logging_enabled:
            raise ValueError("CSV logging is already active")

        # Ensure logs directory exists
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        # Sanitize filename
        if not filename.endswith('.csv'):
            filename += '.csv'

        # Create full path
        csv_path = logs_dir / filename

        try:
            # Open CSV file for writing
            self.csv_file_handle = open(csv_path, 'w', newline='', encoding='utf-8')

            # Define CSV headers
            fieldnames = [
                'time_since_start_seconds',
                'timestamp',
                'pit_temp_c',
                'meat_temp_1_c',
                'meat_temp_2_c',
                'ambient_temp_c',
                'setpoint_c',
                'meat_setpoint_c',
                'damper_percent',
                'pid_output',
                'pid_error',
                'control_mode',
                'safety_shutdown'
            ]

            # Create CSV writer
            self.csv_writer = csv.DictWriter(self.csv_file_handle, fieldnames=fieldnames)
            self.csv_writer.writeheader()

            # Set logging parameters
            with self._lock:
                self.csv_logging_enabled = True
                self.csv_file_path = str(csv_path)
                self.csv_logging_interval = interval_seconds
                self.csv_start_time = time.time()
                self.csv_last_log_time = 0.0

            logging.info(f"CSV logging started: {csv_path} (interval: {interval_seconds}s)")

        except Exception as e:
            # Clean up on error
            if self.csv_file_handle:
                self.csv_file_handle.close()
                self.csv_file_handle = None
            self.csv_writer = None
            raise ValueError(f"Failed to start CSV logging: {e}")

    def stop_csv_logging(self) -> str:
        """Stop CSV logging and return the file path"""
        if not self.csv_logging_enabled:
            raise ValueError("CSV logging is not active")

        file_path = self.csv_file_path

        with self._lock:
            self.csv_logging_enabled = False

        # Close file
        if self.csv_file_handle:
            self.csv_file_handle.close()
            self.csv_file_handle = None

        self.csv_writer = None
        self.csv_file_path = None
        self.csv_start_time = None

        logging.info(f"CSV logging stopped: {file_path}")
        return file_path

    def get_csv_logging_status(self) -> Dict[str, Any]:
        """Get current CSV logging status"""
        with self._lock:
            if self.csv_logging_enabled and self.csv_start_time:
                duration = time.time() - self.csv_start_time
            else:
                duration = 0.0

            return {
                "enabled": self.csv_logging_enabled,
                "file_path": self.csv_file_path,
                "interval_seconds": self.csv_logging_interval,
                "duration_seconds": duration,
                "start_time": datetime.fromtimestamp(self.csv_start_time).isoformat() + "Z" if self.csv_start_time else None
            }

    def _log_csv_data(self) -> None:
        """Log current data to CSV if logging is enabled"""
        if not self.csv_logging_enabled or not self.csv_writer or not self.csv_start_time:
            return

        current_time = time.time()
        time_since_start = current_time - self.csv_start_time

        try:
            # Prepare CSV row data
            csv_row = {
                'time_since_start_seconds': round(time_since_start, 1),
                'timestamp': datetime.now().isoformat() + "Z",
                'pit_temp_c': self.state.pit_temp_c,
                'meat_temp_1_c': self.state.meat_temp_1_c,
                'meat_temp_2_c': self.state.meat_temp_2_c,
                'ambient_temp_c': self.state.ambient_temp_c,
                'setpoint_c': self.state.setpoint_c,
                'meat_setpoint_c': self.state.meat_setpoint_c,
                'damper_percent': self.state.damper_percent,
                'pid_output': self.state.pid_output,
                'pid_error': self.state.pid_error,
                'control_mode': self.state.control_mode,
                'safety_shutdown': self.state.safety_shutdown
            }

            # Write row to CSV
            self.csv_writer.writerow(csv_row)
            self.csv_file_handle.flush()  # Ensure data is written immediately

        except Exception as e:
            logging.error(f"Error writing to CSV: {e}")
            # Don't stop logging on individual write errors

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()