#ifndef CONFIG_H
#define CONFIG_H

// Pin Configuration
#define SERVO_PIN 9            // PWM pin for damper servo
#define PIT_THERMISTOR_PIN A0  // Analog pin for pit temperature probe
#define MEAT_THERMISTOR_PIN \
  A1  // Analog pin for meat temperature probe (optional)

// Servo Configuration
#define SERVO_MIN_ANGLE 60   // Servo angle for 0% damper (closed)
#define SERVO_MAX_ANGLE 120  // Servo angle for 100% damper (open)

// Thermistor Configuration
#define REFERENCE_RESISTOR 10000  // Reference resistor value (10kΩ)
#define NOMINAL_TEMP_C 25.0       // Nominal temperature in Celsius

// Steinhart-Hart Coefficients for typical 10kΩ NTC thermistor
// NTC = Negative Temperature Coefficient (resistance decreases as temperature
// increases) These coefficients are optimized for common NTC thermistors like
// EPCOS B57164K
#define A_COEFF 0.0007343140544
#define B_COEFF 0.0002157437229
#define C_COEFF 0.0000000951568577

// ADC and measurement settings
#define ADC_SAMPLES 10         // Number of ADC samples to average
#define MEASUREMENT_DELAY 100  // Delay between measurements (ms)

// Serial Configuration
#define SERIAL_BAUD 115200    // Must match Python serial_io.py settings
#define JSON_BUFFER_SIZE 256  // Buffer size for JSON messages

// Temperature limits for safety
#define MAX_TEMP_C 400.0  // Maximum reasonable temperature
#define MIN_TEMP_C -20.0  // Minimum reasonable temperature

#endif  // CONFIG_H
