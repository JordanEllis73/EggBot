#include "pid_controller.h"
#include <math.h>

PIDController::PIDController(float kp, float ki, float kd, 
                             float output_min, float output_max)
    : kp_(kp),
      ki_(ki), 
      kd_(kd),
      output_min_(output_min),
      output_max_(output_max),
      last_error_(0.0),
      integral_value_(0.0),
      last_time_(-1.0),
      last_output_(0.0),
      sample_time_ms_(1000),
      initialized_(false) {
  
  // Set integral limits to prevent windup (same as output limits)
  integral_min_ = output_min;
  integral_max_ = output_max;
}

float PIDController::compute(float setpoint, float measurement, unsigned long current_time_ms) {
  // Calculate time delta in seconds
  float dt = 0.0;
  if (last_time_ >= 0.0) {
    dt = (current_time_ms - last_time_) / 1000.0;
  }
  
  // Skip computation if sample time hasn't elapsed
  if (initialized_ && dt < (sample_time_ms_ / 1000.0)) {
    return last_output_;
  }
  
  // Calculate error (how far we are from target)
  float error = setpoint - measurement;
  
  // Proportional term
  float p_term = kp_ * error;
  
  // Integral term (with windup prevention)
  if (dt > 0.0) {
    float potential_integral = integral_value_ + (ki_ * error * dt);
    
    // Prevent integral windup using clamping
    float test_output = p_term + potential_integral;
    if (test_output >= output_min_ && test_output <= output_max_) {
      integral_value_ = potential_integral;
    }
    // If output would be saturated, don't update integral
    
    // Additional integral clamping
    if (integral_value_ > integral_max_) {
      integral_value_ = integral_max_;
    } else if (integral_value_ < integral_min_) {
      integral_value_ = integral_min_;
    }
  }
  
  float i_term = integral_value_;
  
  // Derivative term
  float d_term = 0.0;
  if (initialized_ && dt > 0.0) {
    float derivative = (error - last_error_) / dt;
    d_term = kd_ * derivative;
  }
  
  // Combine all terms
  float output = p_term + i_term + d_term;
  
  // Apply output limits
  if (output > output_max_) {
    output = output_max_;
  } else if (output < output_min_) {
    output = output_min_;
  }
  
  // Save state for next iteration
  last_error_ = error;
  last_time_ = current_time_ms;
  last_output_ = output;
  initialized_ = true;
  
  return output;
}

void PIDController::set_gains(float kp, float ki, float kd) {
  kp_ = kp;
  ki_ = ki;
  kd_ = kd;
}

float* PIDController::get_gains() {
  static float gains[3];
  gains[0] = kp_;
  gains[1] = ki_;
  gains[2] = kd_;
  return gains;
}

void PIDController::set_output_limits(float output_min, float output_max) {
  output_min_ = output_min;
  output_max_ = output_max;
  
  // Update integral limits to match
  integral_min_ = output_min;
  integral_max_ = output_max;
  
  // Clamp current integral if needed
  if (integral_value_ > integral_max_) {
    integral_value_ = integral_max_;
  } else if (integral_value_ < integral_min_) {
    integral_value_ = integral_min_;
  }
}

float* PIDController::get_output_limits() {
  static float limits[2];
  limits[0] = output_min_;
  limits[1] = output_max_;
  return limits;
}

void PIDController::reset() {
  integral_value_ = 0.0;
  last_error_ = 0.0;
  last_time_ = -1.0;
  last_output_ = 0.0;
  initialized_ = false;
}

float PIDController::get_last_output() {
  return last_output_;
}

float PIDController::get_last_error() {
  return last_error_;
}

float PIDController::get_integral_term() {
  return integral_value_;
}

void PIDController::set_sample_time(unsigned long sample_time_ms) {
  if (sample_time_ms > 0) {
    sample_time_ms_ = sample_time_ms;
  }
}

bool PIDController::is_ready() {
  return initialized_;
}