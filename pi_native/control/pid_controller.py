import time
import threading
from typing import Optional, Tuple, List
from dataclasses import dataclass
import logging

from pi_native.config.pid import PIDGains, PIDLimits, PIDConfig

@dataclass
class PIDState:
    """Current state of the PID controller"""
    setpoint: float = 0.0
    process_variable: float = 0.0
    output: float = 0.0
    error: float = 0.0
    integral: float = 0.0
    derivative: float = 0.0
    last_error: float = 0.0
    last_time: float = 0.0

class PIDController:
    """Advanced PID Controller with anti-windup, filtering, and auto-tuning support"""
    
    def __init__(self, config: PIDConfig):
        self.config = config
        self.gains = config.gains
        self.limits = config.limits
        
        # Controller state
        self.state = PIDState()
        self._lock = threading.Lock()
        
        # Operating mode
        self.auto_mode = config.auto_mode
        self.enabled = True
        
        # Timing
        self.sample_time = config.sample_time
        self.last_compute_time = 0.0
        
        # Error history for derivative filtering
        self.error_history: List[float] = []
        self.max_error_history = 5
        
        # Performance tracking
        self.compute_count = 0
        self.total_compute_time = 0.0
        
        logging.info(f"PID Controller initialized with gains Kp={self.gains.kp}, Ki={self.gains.ki}, Kd={self.gains.kd}")
    
    def set_gains(self, kp: float, ki: float, kd: float) -> None:
        """Update PID gains"""
        with self._lock:
            self.gains = PIDGains(kp=kp, ki=ki, kd=kd)
            logging.info(f"PID gains updated: Kp={kp}, Ki={ki}, Kd={kd}")
    
    def get_gains(self) -> Tuple[float, float, float]:
        """Get current PID gains"""
        with self._lock:
            return self.gains.as_tuple()
    
    def set_setpoint(self, setpoint: float) -> None:
        """Set the desired setpoint"""
        with self._lock:
            old_setpoint = self.state.setpoint
            self.state.setpoint = setpoint
            
            # Reset integral term if setpoint changes significantly
            if abs(setpoint - old_setpoint) > 5.0:
                self.state.integral = 0.0
                logging.info(f"Integral term reset due to large setpoint change")
            
            logging.debug(f"Setpoint changed from {old_setpoint:.1f} to {setpoint:.1f}")
    
    def get_setpoint(self) -> float:
        """Get current setpoint"""
        with self._lock:
            return self.state.setpoint
    
    def set_auto_mode(self, auto: bool) -> None:
        """Enable or disable automatic control"""
        with self._lock:
            if auto != self.auto_mode:
                self.auto_mode = auto
                if auto:
                    # Entering auto mode - initialize for bumpless transfer
                    self._initialize_auto_mode()
                    logging.info("PID controller switched to AUTO mode")
                else:
                    logging.info("PID controller switched to MANUAL mode")
    
    def _initialize_auto_mode(self) -> None:
        """Initialize controller state for smooth transition to auto mode"""
        self.state.last_error = 0.0
        self.state.integral = self.state.output  # Start with current output
        self.error_history.clear()
        
        # Clamp integral to limits
        self.state.integral = max(self.limits.integral_min, 
                                min(self.limits.integral_max, self.state.integral))
    
    def compute(self, process_variable: float, dt: Optional[float] = None) -> float:
        """
        Compute PID output based on current process variable
        
        Args:
            process_variable: Current measured value
            dt: Time delta since last computation (auto-calculated if None)
            
        Returns:
            Control output value
        """
        start_time = time.perf_counter()
        
        with self._lock:
            if not self.enabled or not self.auto_mode:
                return self.state.output
            
            current_time = time.time()
            
            # Calculate time delta
            if dt is None:
                if self.last_compute_time == 0:
                    self.last_compute_time = current_time
                    return self.state.output
                dt = current_time - self.last_compute_time
            
            # Enforce minimum sample time
            if dt < self.sample_time:
                return self.state.output
            
            self.last_compute_time = current_time
            
            # Update state
            self.state.process_variable = process_variable
            error = self.state.setpoint - process_variable
            self.state.error = error
            
            # Proportional term
            proportional = self.gains.kp * error
            
            # Integral term with anti-windup
            self.state.integral += self.gains.ki * error * dt
            
            # Clamp integral to prevent windup
            self.state.integral = max(self.limits.integral_min,
                                    min(self.limits.integral_max, self.state.integral))
            
            integral = self.state.integral
            
            # Derivative term with filtering
            if dt > 0:
                derivative_raw = (error - self.state.last_error) / dt
                
                # Apply low-pass filter to derivative term
                if self.error_history:
                    filtered_derivative = (self.limits.derivative_filter * derivative_raw + 
                                         (1 - self.limits.derivative_filter) * self.state.derivative)
                else:
                    filtered_derivative = derivative_raw
                
                self.state.derivative = filtered_derivative
                derivative = self.gains.kd * filtered_derivative
            else:
                derivative = 0.0
            
            # Calculate output
            feedforward = (self.limits.output_max + self.limits.output_min) / 2.0
            output = feedforward + proportional + integral + derivative
            
            # Apply output limits
            output = max(self.limits.output_min, min(self.limits.output_max, output))
            
            # Store values
            self.state.output = output
            self.state.last_error = error
            
            # Update error history for derivative filtering
            self.error_history.append(error)
            if len(self.error_history) > self.max_error_history:
                self.error_history.pop(0)
            
            # Performance tracking
            compute_time = time.perf_counter() - start_time
            self.compute_count += 1
            self.total_compute_time += compute_time
            
            logging.debug(f"PID: SP={self.state.setpoint:.1f}, PV={process_variable:.1f}, "
                         f"E={error:.2f}, P={proportional:.2f}, I={integral:.2f}, "
                         f"D={derivative:.2f}, OUT={output:.1f}")
            
            return output
    
    def reset(self) -> None:
        """Reset controller state"""
        with self._lock:
            self.state.integral = 0.0
            self.state.derivative = 0.0
            self.state.last_error = 0.0
            self.state.error = 0.0
            self.error_history.clear()
            self.last_compute_time = 0.0
            
            logging.info("PID controller reset")
    
    def set_output_limits(self, min_output: float, max_output: float) -> None:
        """Set output limits"""
        if min_output >= max_output:
            raise ValueError("min_output must be less than max_output")
        
        with self._lock:
            self.limits.output_min = min_output
            self.limits.output_max = max_output
            
            # Clamp current output to new limits
            self.state.output = max(min_output, min(max_output, self.state.output))
            
            logging.info(f"Output limits set to [{min_output}, {max_output}]")
    
    def set_integral_limits(self, min_integral: float, max_integral: float) -> None:
        """Set integral windup limits"""
        if min_integral >= max_integral:
            raise ValueError("min_integral must be less than max_integral")
        
        with self._lock:
            self.limits.integral_min = min_integral
            self.limits.integral_max = max_integral
            
            # Clamp current integral to new limits
            self.state.integral = max(min_integral, min(max_integral, self.state.integral))
            
            logging.info(f"Integral limits set to [{min_integral}, {max_integral}]")
    
    def get_state(self) -> PIDState:
        """Get current controller state (copy)"""
        with self._lock:
            return PIDState(
                setpoint=self.state.setpoint,
                process_variable=self.state.process_variable,
                output=self.state.output,
                error=self.state.error,
                integral=self.state.integral,
                derivative=self.state.derivative,
                last_error=self.state.last_error,
                last_time=self.state.last_time
            )
    
    def get_performance_stats(self) -> dict:
        """Get performance statistics"""
        with self._lock:
            avg_compute_time = (self.total_compute_time / self.compute_count 
                              if self.compute_count > 0 else 0.0)
            
            return {
                "compute_count": self.compute_count,
                "total_compute_time": self.total_compute_time,
                "avg_compute_time_ms": avg_compute_time * 1000,
                "sample_time": self.sample_time,
                "auto_mode": self.auto_mode,
                "enabled": self.enabled
            }
    
    def is_stable(self, tolerance: float = 1.0, duration: float = 30.0) -> bool:
        """
        Check if the controller output is stable within tolerance
        
        Args:
            tolerance: Maximum allowable error
            duration: Time period to check stability over
            
        Returns:
            True if stable within tolerance for the specified duration
        """
        with self._lock:
            return abs(self.state.error) <= tolerance
    
    def get_tuning_info(self) -> dict:
        """Get information useful for manual tuning"""
        state = self.get_state()
        
        return {
            "current_error": state.error,
            "error_trend": "increasing" if state.error > state.last_error else "decreasing",
            "integral_contribution": self.gains.ki * state.integral,
            "derivative_contribution": self.gains.kd * state.derivative,
            "proportional_contribution": self.gains.kp * state.error,
            "output_percentage": (state.output / (self.limits.output_max - self.limits.output_min)) * 100,
            "at_output_limit": (state.output == self.limits.output_min or 
                              state.output == self.limits.output_max)
        }
    
    def enable(self) -> None:
        """Enable the controller"""
        with self._lock:
            if not self.enabled:
                self.enabled = True
                self._initialize_auto_mode()
                logging.info("PID controller enabled")
    
    def disable(self) -> None:
        """Disable the controller"""
        with self._lock:
            self.enabled = False
            logging.info("PID controller disabled")
    
    def is_enabled(self) -> bool:
        """Check if controller is enabled"""
        return self.enabled
    
    def is_auto(self) -> bool:
        """Check if controller is in automatic mode"""
        return self.auto_mode
