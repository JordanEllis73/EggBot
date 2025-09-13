import time
import threading
from typing import Optional
import logging

try:
    import pigpio
    PIGPIO_AVAILABLE = True
except ImportError:
    PIGPIO_AVAILABLE = False
    logging.warning("pigpio library not available - running in simulation mode")

class ServoController:
    """Controls servo motor for damper positioning using pigpio"""
    
    def __init__(self, gpio_pin: int = 18, simulate: bool = False):
        self.gpio_pin = gpio_pin
        self.simulate = simulate or not PIGPIO_AVAILABLE
        self._lock = threading.Lock()
        self._pi = None
        self._current_position = 0  # Current servo position (0-100%)
        self._target_position = 0   # Target servo position
        self._last_pulse_width = 0  # Last PWM pulse width sent
        
        # Servo parameters (typical values for standard servos)
        self.min_pulse_width = 500   # Microseconds (0° position)
        self.max_pulse_width = 2500  # Microseconds (180° position) 
        self.center_pulse_width = 1500  # Microseconds (90° position)
        self.pwm_frequency = 50      # Hz (standard servo frequency)
        
        # Movement parameters
        self.max_speed = 20          # Max degrees per second
        self.position_tolerance = 1  # Degrees tolerance for "reached" position
        
        if not self.simulate:
            self._initialize_pigpio()
        
        # Start position control thread
        self._running = True
        self._control_thread = threading.Thread(target=self._position_control_loop, daemon=True)
        self._control_thread.start()
        
        logging.info(f"ServoController initialized on GPIO {self.gpio_pin} (simulate={self.simulate})")
    
    def _initialize_pigpio(self) -> None:
        """Initialize pigpio connection"""
        try:
            self._pi = pigpio.pi()
            if not self._pi.connected:
                raise RuntimeError("Failed to connect to pigpio daemon")
            
            # Set servo to center position initially
            self.set_position_percent(0)  # Start at 0% (closed damper)
            
            logging.info(f"pigpio connected successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize pigpio: {e}")
            self.simulate = True
            logging.warning("Falling back to simulation mode")
    
    def _percent_to_pulse_width(self, percent: float) -> int:
        """Convert percentage (0-100) to pulse width in microseconds"""
        percent = max(0, min(100, percent))  # Clamp to 0-100%
        
        # Map 0-100% to min-max pulse width
        pulse_width = self.min_pulse_width + (percent / 100.0) * (self.max_pulse_width - self.min_pulse_width)
        return int(pulse_width)
    
    def _pulse_width_to_percent(self, pulse_width: int) -> float:
        """Convert pulse width to percentage"""
        if pulse_width < self.min_pulse_width:
            return 0.0
        if pulse_width > self.max_pulse_width:
            return 100.0
        
        percent = ((pulse_width - self.min_pulse_width) / (self.max_pulse_width - self.min_pulse_width)) * 100.0
        return percent
    
    def _set_pwm(self, pulse_width: int) -> None:
        """Set PWM signal to servo"""
        if self.simulate:
            self._last_pulse_width = pulse_width
            return
        
        if self._pi and self._pi.connected:
            self._pi.set_servo_pulsewidth(self.gpio_pin, pulse_width)
            self._last_pulse_width = pulse_width
    
    def set_position_percent(self, percent: float) -> None:
        """Set servo position as percentage (0-100%)"""
        percent = max(0, min(100, percent))
        
        with self._lock:
            self._target_position = percent
            
        logging.debug(f"Servo target position set to {percent}%")
    
    def get_position_percent(self) -> float:
        """Get current servo position as percentage"""
        with self._lock:
            return self._current_position
    
    def get_target_position_percent(self) -> float:
        """Get target servo position as percentage"""
        with self._lock:
            return self._target_position
    
    def is_at_target(self) -> bool:
        """Check if servo is at target position within tolerance"""
        with self._lock:
            diff = abs(self._current_position - self._target_position)
            return diff <= self.position_tolerance
    
    def _position_control_loop(self) -> None:
        """Background thread for smooth servo movement"""
        while self._running:
            try:
                with self._lock:
                    current = self._current_position
                    target = self._target_position
                
                if abs(current - target) > self.position_tolerance:
                    # Calculate movement step based on max speed
                    max_step = self.max_speed * 0.05  # 50ms update rate = 20Hz
                    
                    if target > current:
                        step = min(max_step, target - current)
                        new_position = current + step
                    else:
                        step = min(max_step, current - target)
                        new_position = current - step
                    
                    # Update servo position
                    pulse_width = self._percent_to_pulse_width(new_position)
                    self._set_pwm(pulse_width)
                    
                    with self._lock:
                        self._current_position = new_position
                    
                    logging.debug(f"Servo moved to {new_position:.1f}% (pulse: {pulse_width}μs)")
                
                time.sleep(0.05)  # 50ms update rate
                
            except Exception as e:
                logging.error(f"Error in servo control loop: {e}")
                time.sleep(0.1)
    
    def set_calibration(self, min_pulse: int, max_pulse: int, center_pulse: Optional[int] = None) -> None:
        """Set servo calibration parameters"""
        if min_pulse >= max_pulse:
            raise ValueError("min_pulse must be less than max_pulse")
        
        self.min_pulse_width = min_pulse
        self.max_pulse_width = max_pulse
        
        if center_pulse:
            self.center_pulse_width = center_pulse
        else:
            self.center_pulse_width = (min_pulse + max_pulse) // 2
        
        logging.info(f"Servo calibrated: min={min_pulse}μs, max={max_pulse}μs, center={self.center_pulse_width}μs")
    
    def center_servo(self) -> None:
        """Move servo to center position (50%)"""
        self.set_position_percent(50)
    
    def stop_servo(self) -> None:
        """Stop PWM signal to servo (servo will lose holding torque)"""
        if not self.simulate and self._pi and self._pi.connected:
            self._pi.set_servo_pulsewidth(self.gpio_pin, 0)
        self._last_pulse_width = 0
        logging.debug("Servo PWM stopped")
    
    def get_pulse_width(self) -> int:
        """Get current PWM pulse width in microseconds"""
        return self._last_pulse_width
    
    def test_sweep(self, cycles: int = 1, delay: float = 2.0) -> None:
        """Test servo by sweeping from 0% to 100% and back"""
        logging.info(f"Starting servo test sweep ({cycles} cycles)")
        
        for cycle in range(cycles):
            logging.info(f"Sweep cycle {cycle + 1}/{cycles}")
            
            # Move to 0%
            self.set_position_percent(0)
            time.sleep(delay)
            
            # Move to 100% 
            self.set_position_percent(100)
            time.sleep(delay)
            
            # Move to 50%
            self.set_position_percent(50)
            time.sleep(delay)
        
        logging.info("Servo test sweep completed")
    
    def close(self) -> None:
        """Clean up resources and stop servo"""
        self._running = False
        
        if self._control_thread.is_alive():
            self._control_thread.join(timeout=1.0)
        
        self.stop_servo()
        
        if not self.simulate and self._pi and self._pi.connected:
            self._pi.stop()
        
        logging.info("ServoController closed")
    
    def __del__(self):
        """Ensure cleanup on deletion"""
        try:
            self.close()
        except Exception:
            pass