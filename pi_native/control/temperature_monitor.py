import time
import threading
from typing import Dict, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
import logging

from pi_native.hardware.ads1115_manager import ADS1115Manager, ProbeReading
from pi_native.hardware.thermistor_calc import ThermistorCalculator
from pi_native.config.hardware import hardware_config
from pi_native.config.pid import SafetyLimits

@dataclass
class TemperatureReading:
    """Temperature reading with metadata"""
    channel: int
    probe_name: str
    temperature_c: float
    voltage: float
    timestamp: datetime
    is_valid: bool = True
    error_message: Optional[str] = None

@dataclass
class ProbeStatus:
    """Status information for a temperature probe"""
    probe_name: str
    channel: int
    is_connected: bool = False
    last_reading: Optional[TemperatureReading] = None
    last_update: Optional[datetime] = None
    consecutive_errors: int = 0
    total_readings: int = 0
    average_temp: float = 0.0
    min_temp: float = float('inf')
    max_temp: float = float('-inf')
    temperature_history: List[float] = field(default_factory=list)

class TemperatureMonitor:
    """Monitors multiple temperature probes and provides safety features"""
    
    def __init__(self, 
                 update_interval: float = 0.5,
                 safety_limits: Optional[SafetyLimits] = None,
                 simulate: bool = False):
        
        self.update_interval = update_interval
        self.safety_limits = safety_limits or SafetyLimits()
        self.simulate = simulate
        
        # Hardware components
        self.adc = ADS1115Manager(simulate=simulate)
        self.calculator = ThermistorCalculator()
        
        # Initialize probe configurations
        for channel in range(4):
            config = hardware_config.get_probe_config(channel)
            self.calculator.set_probe_config(channel, config)
        
        # Probe status tracking
        self.probes: Dict[str, ProbeStatus] = {}
        self._initialize_probes()
        
        # Safety and alerts
        self.alert_callbacks: List[Callable[[str, str], None]] = []
        self.safety_shutdown = False
        
        # Threading
        self._lock = threading.Lock()
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        
        # Temperature filtering
        self.filter_alpha = 0.7  # Low-pass filter coefficient
        self.max_temp_change_per_second = 10.0  # °C/s maximum reasonable change
        
        logging.info(f"TemperatureMonitor initialized with {len(self.probes)} probes")
    
    def _initialize_probes(self) -> None:
        """Initialize probe status objects"""
        for channel, probe_name in hardware_config.PROBE_CHANNEL_MAP.items():
            self.probes[probe_name] = ProbeStatus(
                probe_name=probe_name,
                channel=channel
            )
    
    def add_alert_callback(self, callback: Callable[[str, str], None]) -> None:
        """Add callback for safety alerts (level, message)"""
        self.alert_callbacks.append(callback)
    
    def _trigger_alert(self, level: str, message: str) -> None:
        """Trigger alert callbacks"""
        logging.warning(f"ALERT [{level}]: {message}")
        for callback in self.alert_callbacks:
            try:
                callback(level, message)
            except Exception as e:
                logging.error(f"Error in alert callback: {e}")
    
    def start_monitoring(self) -> None:
        """Start the temperature monitoring thread"""
        if self._running:
            return
        
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        logging.info("Temperature monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop the temperature monitoring thread"""
        self._running = False
        
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2.0)
        
        logging.info("Temperature monitoring stopped")
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop"""
        while self._running:
            try:
                start_time = time.time()
                
                # Read all channels
                readings = self.adc.read_all_channels()
                
                # Process each reading
                temp_readings: Dict[str, TemperatureReading] = {}
                
                for channel, adc_reading in readings.items():
                    temp_reading = self._process_reading(channel, adc_reading)
                    if temp_reading:
                        probe_name = hardware_config.PROBE_CHANNEL_MAP[channel]
                        temp_readings[probe_name] = temp_reading
                
                # Update probe status and check safety
                with self._lock:
                    for probe_name, temp_reading in temp_readings.items():
                        self._update_probe_status(probe_name, temp_reading)
                    
                    self._check_safety()
                
                # Maintain loop timing
                elapsed = time.time() - start_time
                sleep_time = max(0, self.update_interval - elapsed)
                time.sleep(sleep_time)
                
            except Exception as e:
                logging.error(f"Error in temperature monitor loop: {e}")
                time.sleep(1.0)  # Error recovery delay
    
    def _process_reading(self, channel: int, adc_reading: ProbeReading) -> Optional[TemperatureReading]:
        """Process ADC reading into temperature reading"""
        try:
            probe_name = hardware_config.PROBE_CHANNEL_MAP[channel]
            
            # Convert voltage to temperature
            temp_c = self.calculator.voltage_to_temperature(adc_reading.voltage, channel)
            
            if temp_c is None:
                return TemperatureReading(
                    channel=channel,
                    probe_name=probe_name,
                    temperature_c=0.0,
                    voltage=adc_reading.voltage,
                    timestamp=datetime.now(),
                    is_valid=False,
                    error_message="Temperature conversion failed"
                )
            
            # Validate reading
            is_valid = self.calculator.validate_reading(temp_c, channel)
            error_msg = None if is_valid else "Reading outside valid range"
            
            return TemperatureReading(
                channel=channel,
                probe_name=probe_name,
                temperature_c=temp_c,
                voltage=adc_reading.voltage,
                timestamp=datetime.now(),
                is_valid=is_valid,
                error_message=error_msg
            )
            
        except Exception as e:
            probe_name = hardware_config.PROBE_CHANNEL_MAP.get(channel, f"Channel_{channel}")
            logging.error(f"Error processing reading for {probe_name}: {e}")
            return None
    
    def _update_probe_status(self, probe_name: str, reading: TemperatureReading) -> None:
        """Update probe status with new reading"""
        probe = self.probes[probe_name]
        
        # Apply temperature filtering if we have a previous reading
        filtered_temp = reading.temperature_c
        if probe.last_reading and reading.is_valid:
            # Check for unreasonable temperature jumps
            temp_diff = abs(reading.temperature_c - probe.last_reading.temperature_c)
            time_diff = (reading.timestamp - probe.last_reading.timestamp).total_seconds()
            
            if time_diff > 0:
                temp_rate = temp_diff / time_diff
                if temp_rate > self.max_temp_change_per_second:
                    # Apply more aggressive filtering for large changes
                    alpha = 0.3
                else:
                    alpha = self.filter_alpha
                
                filtered_temp = (alpha * reading.temperature_c + 
                               (1 - alpha) * probe.last_reading.temperature_c)
        
        # Update reading with filtered temperature
        reading.temperature_c = filtered_temp
        
        # Update probe status
        probe.last_reading = reading
        probe.last_update = reading.timestamp
        probe.total_readings += 1
        
        if reading.is_valid:
            probe.consecutive_errors = 0
            probe.is_connected = True
            
            # Update statistics
            probe.min_temp = min(probe.min_temp, reading.temperature_c)
            probe.max_temp = max(probe.max_temp, reading.temperature_c)
            
            # Update temperature history (keep last 100 readings)
            probe.temperature_history.append(reading.temperature_c)
            if len(probe.temperature_history) > 100:
                probe.temperature_history.pop(0)
            
            # Calculate rolling average
            if probe.temperature_history:
                probe.average_temp = sum(probe.temperature_history) / len(probe.temperature_history)
        else:
            probe.consecutive_errors += 1
            if probe.consecutive_errors > 5:
                probe.is_connected = False
                self._trigger_alert("WARNING", 
                                  f"Probe {probe_name} appears disconnected ({probe.consecutive_errors} consecutive errors)")
    
    def _check_safety(self) -> None:
        """Check safety limits and trigger alerts"""
        pit_probe = self.probes.get("pit_probe")
        
        if pit_probe and pit_probe.last_reading and pit_probe.last_reading.is_valid:
            pit_temp = pit_probe.last_reading.temperature_c
            
            # Check maximum temperature
            if pit_temp > self.safety_limits.max_pit_temp:
                self._trigger_alert("CRITICAL", 
                                  f"Pit temperature {pit_temp:.1f}°C exceeds maximum {self.safety_limits.max_pit_temp}°C")
                self.safety_shutdown = True
            
            # Check high temperature warning
            elif pit_temp > self.safety_limits.high_temp_warning:
                self._trigger_alert("WARNING", 
                                  f"Pit temperature {pit_temp:.1f}°C approaching maximum")
            
            # Check temperature rate of change
            if len(pit_probe.temperature_history) >= 2:
                recent_temps = pit_probe.temperature_history[-10:]  # Last 10 readings
                if len(recent_temps) >= 2:
                    temp_rate = (recent_temps[-1] - recent_temps[0]) / (len(recent_temps) * self.update_interval / 60.0)  # °C/min
                    
                    if temp_rate > self.safety_limits.temp_rate_limit:
                        self._trigger_alert("WARNING", 
                                          f"Temperature rising rapidly: {temp_rate:.1f}°C/min")
        
        # Check for disconnected probes
        for probe_name, probe in self.probes.items():
            if probe.last_update:
                seconds_since_update = (datetime.now() - probe.last_update).total_seconds()
                
                if seconds_since_update > self.safety_limits.probe_timeout:
                    self._trigger_alert("WARNING", 
                                      f"Probe {probe_name} timeout - no reading for {seconds_since_update:.1f}s")
    
    def get_current_temperatures(self) -> Dict[str, Optional[float]]:
        """Get current temperature readings for all probes"""
        with self._lock:
            temps = {}
            for probe_name, probe in self.probes.items():
                if probe.last_reading and probe.last_reading.is_valid:
                    temps[probe_name] = probe.last_reading.temperature_c
                else:
                    temps[probe_name] = None
            return temps
    
    def get_probe_status(self, probe_name: str) -> Optional[ProbeStatus]:
        """Get status for a specific probe"""
        with self._lock:
            return self.probes.get(probe_name)
    
    def get_all_probe_status(self) -> Dict[str, ProbeStatus]:
        """Get status for all probes"""
        with self._lock:
            return self.probes.copy()
    
    def get_pit_temperature(self) -> Optional[float]:
        """Get current pit temperature (primary control variable)"""
        temps = self.get_current_temperatures()
        return temps.get("pit_probe")
    
    def get_meat_temperatures(self) -> Dict[str, Optional[float]]:
        """Get current meat probe temperatures"""
        temps = self.get_current_temperatures()
        return {
            "meat_probe_1": temps.get("meat_probe_1"),
            "meat_probe_2": temps.get("meat_probe_2")
        }
    
    def calibrate_probe(self, probe_name: str, actual_temperature: float) -> None:
        """Calibrate a probe based on known actual temperature"""
        probe = self.probes.get(probe_name)
        if not probe or not probe.last_reading or not probe.last_reading.is_valid:
            raise ValueError(f"Cannot calibrate {probe_name}: no valid reading available")
        
        channel = probe.channel
        measured_temp = probe.last_reading.temperature_c
        
        self.calculator.calibrate_probe(channel, measured_temp, actual_temperature)
        
        # Update hardware config
        config = self.calculator.get_probe_config(channel)
        hardware_config.set_probe_config(channel, config)
        
        logging.info(f"Probe {probe_name} calibrated: offset = {config.offset_c:.2f}°C")
    
    def is_safety_shutdown(self) -> bool:
        """Check if system is in safety shutdown mode"""
        return self.safety_shutdown
    
    def reset_safety_shutdown(self) -> None:
        """Reset safety shutdown flag (after addressing the issue)"""
        self.safety_shutdown = False
        logging.info("Safety shutdown reset")
    
    def get_temperature_trend(self, probe_name: str, minutes: int = 5) -> Optional[str]:
        """Get temperature trend for a probe over specified time period"""
        probe = self.probes.get(probe_name)
        if not probe or not probe.temperature_history:
            return None
        
        history = probe.temperature_history
        samples_needed = max(2, int(minutes * 60 / self.update_interval))
        
        if len(history) < samples_needed:
            return "insufficient_data"
        
        recent_temps = history[-samples_needed:]
        start_temp = sum(recent_temps[:3]) / 3  # Average of first 3
        end_temp = sum(recent_temps[-3:]) / 3   # Average of last 3
        
        temp_change = end_temp - start_temp
        
        if abs(temp_change) < 0.5:
            return "stable"
        elif temp_change > 0:
            return "rising"
        else:
            return "falling"
    
    def close(self) -> None:
        """Clean up resources"""
        self.stop_monitoring()
        if self.adc:
            self.adc.close()
        logging.info("TemperatureMonitor closed")