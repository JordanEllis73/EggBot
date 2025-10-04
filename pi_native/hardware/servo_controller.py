import time
import threading
from typing import Optional, Dict, Any
import logging
import socket

try:
    import pigpio
    PIGPIO_AVAILABLE = True
except ImportError:
    PIGPIO_AVAILABLE = False
    logging.warning("pigpio library not available - running in simulation mode")

from pi_native.config.hardware import ServoConfig

class ServoController:
    """Controls servo motor for damper positioning using pigpio"""
    
    def __init__(self, gpio_pin: int = 18, simulate: bool = False, config: Optional[ServoConfig] = None,
                 pigpio_host: str = "pigpiod", pigpio_port: int = 8888):
        self.gpio_pin = gpio_pin
        self.simulate = simulate or not PIGPIO_AVAILABLE
        self.pigpio_host = pigpio_host
        self.pigpio_port = pigpio_port
        self._lock = threading.Lock()
        self._pi = None
        self._current_position = 0  # Current servo position (0-100%)
        self._target_position = 0   # Target servo position
        self._last_pulse_width = 0  # Last PWM pulse width sent

        # Connection monitoring
        self._connection_attempts = 0
        self._max_connection_attempts = 10
        self._connection_retry_delay = 2.0
        self._last_connection_attempt = 0
        self._connection_lost_count = 0
        self._last_successful_command = 0

        # Servo health monitoring
        self._command_success_count = 0
        self._command_failure_count = 0
        self._last_health_check = 0
        self._health_check_interval = 30.0  # Check every 30 seconds

        # Use provided config or create default ServoConfig
        if config is None:
            config = ServoConfig()

        # Servo parameters from config
        self.min_pulse_width = config.min_pulse_width
        self.max_pulse_width = config.max_pulse_width
        self.center_pulse_width = config.center_pulse_width
        self.pwm_frequency = config.pwm_frequency

        # Movement parameters from config
        self.max_speed = config.max_speed
        self.position_tolerance = config.position_tolerance

        if not self.simulate:
            self._initialize_pigpio()

        # Start position control thread
        self._running = True
        self._control_thread = threading.Thread(target=self._position_control_loop, daemon=True)
        self._control_thread.start()

        logging.info(f"ServoController initialized on GPIO {self.gpio_pin} (simulate={self.simulate})")
        logging.info(f"Servo config: min={self.min_pulse_width}μs, max={self.max_pulse_width}μs, center={self.center_pulse_width}μs, speed={self.max_speed}°/s")
        logging.info(f"pigpio connection: host={self.pigpio_host}, port={self.pigpio_port}")
    
    def _initialize_pigpio(self) -> None:
        """Initialize pigpio connection with retry logic"""
        self._connection_attempts = 0

        while self._connection_attempts < self._max_connection_attempts:
            try:
                self._connection_attempts += 1
                self._last_connection_attempt = time.time()

                logging.info(f"Attempting pigpio connection {self._connection_attempts}/{self._max_connection_attempts} to {self.pigpio_host}:{self.pigpio_port}")

                # Test socket connection first
                self._test_pigpio_socket()

                # Connect to pigpio daemon
                self._pi = pigpio.pi(host=self.pigpio_host, port=self.pigpio_port)

                if not self._pi.connected:
                    raise RuntimeError(f"pigpio connection failed - daemon not responding")

                # Test GPIO access
                version = self._pi.get_pigpio_version()
                logging.info(f"Connected to pigpio daemon version {version}")

                # Test servo control
                self._test_servo_control()

                # Set servo to initial position
                self.set_position_percent(0)  # Start at 0% (closed damper)

                self._last_successful_command = time.time()
                logging.info(f"pigpio connection established successfully on attempt {self._connection_attempts}")
                return

            except Exception as e:
                logging.warning(f"pigpio connection attempt {self._connection_attempts} failed: {e}")

                if self._pi:
                    try:
                        self._pi.stop()
                    except:
                        pass
                    self._pi = None

                if self._connection_attempts < self._max_connection_attempts:
                    logging.info(f"Retrying in {self._connection_retry_delay} seconds...")
                    time.sleep(self._connection_retry_delay)
                else:
                    logging.error(f"Failed to connect to pigpio after {self._max_connection_attempts} attempts")
                    self.simulate = True
                    logging.warning("Falling back to simulation mode")

    def _test_pigpio_socket(self) -> None:
        """Test if pigpio daemon is listening on the expected port"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            result = sock.connect_ex((self.pigpio_host, self.pigpio_port))
            sock.close()

            if result != 0:
                raise ConnectionError(f"Cannot connect to {self.pigpio_host}:{self.pigpio_port}")

        except Exception as e:
            raise ConnectionError(f"Socket test failed: {e}")

    def _test_servo_control(self) -> None:
        """Test basic servo control functionality"""
        try:
            # Test setting servo pulse width
            test_pulse = self.center_pulse_width
            self._pi.set_servo_pulsewidth(self.gpio_pin, test_pulse)
            time.sleep(0.1)

            # Test reading pulse width back (if supported)
            try:
                current_pulse = self._pi.get_servo_pulsewidth(self.gpio_pin)
                logging.debug(f"Servo test: set {test_pulse}μs, read {current_pulse}μs")
            except Exception:
                logging.debug("Cannot read servo pulse width (normal for some setups)")

            # Reset to off state
            self._pi.set_servo_pulsewidth(self.gpio_pin, 0)

        except Exception as e:
            raise RuntimeError(f"Servo control test failed: {e}")

    def _reconnect_pigpio(self) -> bool:
        """Attempt to reconnect to pigpio daemon"""
        logging.warning("Attempting to reconnect to pigpio daemon...")

        # Clean up existing connection
        if self._pi:
            try:
                self._pi.stop()
            except:
                pass
            self._pi = None

        # Reset simulation mode and try to reconnect
        self.simulate = False
        self._initialize_pigpio()

        return not self.simulate
    
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
    
    def _set_pwm(self, pulse_width: int) -> bool:
        """Set PWM signal to servo with error handling"""
        if self.simulate:
            self._last_pulse_width = pulse_width
            return True

        try:
            if not self._pi or not self._pi.connected:
                logging.warning("pigpio not connected - attempting reconnection")
                if not self._reconnect_pigpio():
                    return False

            # Send servo command
            result = self._pi.set_servo_pulsewidth(self.gpio_pin, pulse_width)

            if result != 0:
                logging.error(f"Servo command failed with code {result}")
                self._command_failure_count += 1
                return False

            self._last_pulse_width = pulse_width
            self._last_successful_command = time.time()
            self._command_success_count += 1

            logging.debug(f"Servo PWM set to {pulse_width}μs successfully")
            return True

        except Exception as e:
            logging.error(f"Failed to set servo PWM: {e}")
            self._command_failure_count += 1
            self._connection_lost_count += 1

            # Try to reconnect if connection seems lost
            if self._connection_lost_count > 3:
                logging.warning("Multiple command failures - attempting reconnection")
                self._reconnect_pigpio()
                self._connection_lost_count = 0

            return False
    
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

                # Perform periodic health checks
                self._perform_health_check()

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

    def _perform_health_check(self) -> None:
        """Perform periodic health check of servo connection"""
        current_time = time.time()

        if (current_time - self._last_health_check) < self._health_check_interval:
            return

        self._last_health_check = current_time

        if self.simulate:
            return

        try:
            # Test pigpio connection
            if not self._pi or not self._pi.connected:
                logging.warning("Health check: pigpio not connected")
                self._reconnect_pigpio()
                return

            # Test servo responsiveness by reading version (lightweight test)
            version = self._pi.get_pigpio_version()
            logging.debug(f"Health check: pigpio version {version}")

            # Check if we've had recent successful commands
            time_since_last_success = current_time - self._last_successful_command
            if time_since_last_success > 300:  # 5 minutes
                logging.warning(f"Health check: No successful servo commands for {time_since_last_success:.0f} seconds")

            # Log statistics
            total_commands = self._command_success_count + self._command_failure_count
            if total_commands > 0:
                success_rate = (self._command_success_count / total_commands) * 100
                logging.debug(f"Health check: Command success rate: {success_rate:.1f}% ({self._command_success_count}/{total_commands})")

        except Exception as e:
            logging.warning(f"Health check failed: {e}")
            self._reconnect_pigpio()

    def get_servo_diagnostics(self) -> Dict[str, Any]:
        """Get comprehensive servo diagnostics information"""
        current_time = time.time()
        total_commands = self._command_success_count + self._command_failure_count

        diagnostics = {
            # Connection status
            "connected": not self.simulate and self._pi and self._pi.connected,
            "simulate_mode": self.simulate,
            "pigpio_host": self.pigpio_host,
            "pigpio_port": self.pigpio_port,

            # Connection attempts
            "connection_attempts": self._connection_attempts,
            "max_connection_attempts": self._max_connection_attempts,
            "last_connection_attempt": self._last_connection_attempt,
            "connection_lost_count": self._connection_lost_count,

            # Command statistics
            "command_success_count": self._command_success_count,
            "command_failure_count": self._command_failure_count,
            "total_commands": total_commands,
            "success_rate": (self._command_success_count / total_commands * 100) if total_commands > 0 else 0,

            # Timing
            "last_successful_command": self._last_successful_command,
            "time_since_last_success": current_time - self._last_successful_command,
            "last_health_check": self._last_health_check,

            # Current servo state
            "current_position_percent": self._current_position,
            "target_position_percent": self._target_position,
            "last_pulse_width": self._last_pulse_width,
            "gpio_pin": self.gpio_pin,

            # Configuration
            "min_pulse_width": self.min_pulse_width,
            "max_pulse_width": self.max_pulse_width,
            "center_pulse_width": self.center_pulse_width,
            "pwm_frequency": self.pwm_frequency,
            "max_speed": self.max_speed,
            "position_tolerance": self.position_tolerance,
        }

        # Add pigpio version if connected
        if not self.simulate and self._pi and self._pi.connected:
            try:
                diagnostics["pigpio_version"] = self._pi.get_pigpio_version()
            except Exception as e:
                diagnostics["pigpio_version_error"] = str(e)

        return diagnostics

    def test_servo_connectivity(self) -> Dict[str, Any]:
        """Test servo connectivity and return detailed results"""
        test_results = {
            "test_timestamp": time.time(),
            "overall_success": False,
            "tests": {}
        }

        try:
            # Test 1: Socket connectivity
            test_results["tests"]["socket_connection"] = self._test_socket_connectivity()

            # Test 2: pigpio daemon connection
            test_results["tests"]["pigpio_connection"] = self._test_pigpio_connectivity()

            # Test 3: Servo control
            test_results["tests"]["servo_control"] = self._test_servo_functionality()

            # Overall result
            test_results["overall_success"] = all(
                result.get("success", False) for result in test_results["tests"].values()
            )

        except Exception as e:
            test_results["error"] = str(e)

        return test_results

    def _test_socket_connectivity(self) -> Dict[str, Any]:
        """Test socket connection to pigpio daemon"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            start_time = time.time()
            result = sock.connect_ex((self.pigpio_host, self.pigpio_port))
            connect_time = time.time() - start_time
            sock.close()

            return {
                "success": result == 0,
                "connect_time_ms": connect_time * 1000,
                "error": f"Connection failed (code {result})" if result != 0 else None
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _test_pigpio_connectivity(self) -> Dict[str, Any]:
        """Test pigpio daemon connectivity"""
        try:
            test_pi = pigpio.pi(host=self.pigpio_host, port=self.pigpio_port)

            if not test_pi.connected:
                test_pi.stop()
                return {
                    "success": False,
                    "error": "pigpio daemon not responding"
                }

            version = test_pi.get_pigpio_version()
            test_pi.stop()

            return {
                "success": True,
                "pigpio_version": version
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _test_servo_functionality(self) -> Dict[str, Any]:
        """Test basic servo functionality"""
        if self.simulate:
            return {
                "success": True,
                "note": "Simulation mode - no actual servo test"
            }

        try:
            if not self._pi or not self._pi.connected:
                return {
                    "success": False,
                    "error": "No pigpio connection"
                }

            # Test setting a servo pulse
            test_pulse = self.center_pulse_width
            result = self._pi.set_servo_pulsewidth(self.gpio_pin, test_pulse)

            if result != 0:
                return {
                    "success": False,
                    "error": f"Servo command failed with code {result}"
                }

            # Try to read back (if supported)
            try:
                read_pulse = self._pi.get_servo_pulsewidth(self.gpio_pin)
                pulse_match = abs(read_pulse - test_pulse) < 10  # Allow 10μs tolerance
            except:
                read_pulse = None
                pulse_match = None

            # Reset servo
            self._pi.set_servo_pulsewidth(self.gpio_pin, 0)

            return {
                "success": True,
                "test_pulse_sent": test_pulse,
                "test_pulse_read": read_pulse,
                "pulse_match": pulse_match
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

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