#ifndef PID_CONTROLLER_H
#define PID_CONTROLLER_H

#include "Arduino.h"
#include "config.h"

/**
 * PID Controller for automatic damper control
 * 
 * This class implements a PID (Proportional-Integral-Derivative) controller
 * for maintaining temperature by automatically adjusting the damper position.
 */
class PIDController {
 private:
  // PID gains
  float kp_, ki_, kd_;
  
  // Output limits
  float output_min_, output_max_;
  
  // Internal state
  float last_error_;
  float integral_value_;
  float last_time_;
  float last_output_;
  
  // Integral windup prevention
  float integral_min_, integral_max_;
  
  // Sample time tracking
  unsigned long sample_time_ms_;
  
  bool initialized_;

 public:
  /**
   * Constructor
   * @param kp - Proportional gain
   * @param ki - Integral gain  
   * @param kd - Derivative gain
   * @param output_min - Minimum output value (0%)
   * @param output_max - Maximum output value (100%)
   */
  PIDController(float kp = 1.0, float ki = 0.1, float kd = 0.05, 
                float output_min = 0.0, float output_max = 100.0);
  
  /**
   * Calculate PID output for temperature control
   * @param setpoint - Desired temperature (°C)
   * @param measurement - Actual temperature (°C)
   * @param current_time_ms - Current time in milliseconds
   * @return PID output (damper percentage 0-100%)
   */
  float compute(float setpoint, float measurement, unsigned long current_time_ms);
  
  /**
   * Set PID gains
   * @param kp - Proportional gain
   * @param ki - Integral gain
   * @param kd - Derivative gain
   */
  void set_gains(float kp, float ki, float kd);
  
  /**
   * Get current PID gains
   * @return Array of gains [kp, ki, kd]
   */
  float* get_gains();
  
  /**
   * Set output limits
   * @param output_min - Minimum output value
   * @param output_max - Maximum output value
   */
  void set_output_limits(float output_min, float output_max);
  
  /**
   * Get output limits
   * @return Array of limits [min, max]
   */
  float* get_output_limits();
  
  /**
   * Reset controller state
   * Clears integral term and error history
   */
  void reset();
  
  /**
   * Get last calculated output
   * @return Last PID output value
   */
  float get_last_output();
  
  /**
   * Get current error (setpoint - measurement)
   * @return Current error value
   */
  float get_last_error();
  
  /**
   * Get integral term value
   * @return Current integral term
   */
  float get_integral_term();
  
  /**
   * Set sample time in milliseconds
   * @param sample_time_ms - Sample time in ms (default 1000ms)
   */
  void set_sample_time(unsigned long sample_time_ms);
  
  /**
   * Check if controller is ready
   * @return true if initialized and ready to compute
   */
  bool is_ready();
};

#endif  // PID_CONTROLLER_H
