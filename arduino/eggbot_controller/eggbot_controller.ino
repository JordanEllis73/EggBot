/**
 * EggBot Controller - Arduino Uno Firmware
 *
 * This firmware implements the serial protocol for communicating with the EggBot
 * Python API. It controls a servo for damper position and reads thermistors for
 * temperature monitoring using the Steinhart-Hart equation.
 *
 * Hardware Requirements:
 * - Arduino Uno or compatible
 * - Servo motor for damper control (connected to pin 9)
 * - 10kΩ NTC thermistors for temperature sensing
 * - 10kΩ reference resistors for voltage dividers
 *
 * Serial Protocol:
 * - Baud: 115200
 * - Format: JSON messages terminated with newline
 * - Incoming: {"setpoint_c": 110.0}, {"damper_percent": 50}, etc.
 * - Outgoing: {"pit_temp_c": 125.5, "meat_temp_c": 65.2}
 */

#include <Servo.h>
#include <ArduinoJson.h>
#include "config.h"
#include "thermistor.h"
#include "pid_controller.h"

// Global objects
Servo damperServo;
Thermistor pitThermistor(PIT_THERMISTOR_PIN);
Thermistor meatThermistor(MEAT_THERMISTOR_PIN);
PIDController pidController(1.0, 0.1, 0.05, 0.0, 100.0); // P, I, D, min%, max%

// Control mode state
bool manualControl = true;
float setpointC = 110.0;
float meatSetpointC = 98.0;
int damperPercent = 0;
float pidGains[3] = {1.0, 0.1, 0.05}; // P, I, D

// PID control timing
unsigned long lastPidUpdate = 0;
const unsigned long PID_INTERVAL = 5000;  // Update PID every 5 seconds

// Timing variables
unsigned long lastTempReading = 0;
unsigned long lastStatusSend = 0;
const unsigned long TEMP_INTERVAL = 1000;    // Read temperatures every 1 second
const unsigned long STATUS_INTERVAL = 250;  // Send status every 250ms for faster UI response

// JSON buffer
StaticJsonDocument<JSON_BUFFER_SIZE> jsonDoc;
char jsonBuffer[JSON_BUFFER_SIZE];

void setup() {
  Serial.begin(SERIAL_BAUD);

  // Initialize servo
  damperServo.attach(SERVO_PIN);
  setDamperPosition(damperPercent); // Start with damper closed

  // Initialize thermistor pins
  pinMode(PIT_THERMISTOR_PIN, INPUT);
  pinMode(MEAT_THERMISTOR_PIN, INPUT);

  // Send startup message
  Serial.println("{\"status\":\"Arduino EggBot Controller Ready\",\"version\":\"1.0\"}");

  delay(1000); // Allow time for serial connection to stabilize
}

void loop() {
  unsigned long currentTime = millis();

  // Process incoming serial commands
  processSerialCommands();

  // Send temperature status periodically
  if (currentTime - lastStatusSend >= STATUS_INTERVAL) {
    sendTemperatureStatus();
    lastStatusSend = currentTime;
  }

  // Handle automatic PID control
  if (!manualControl && currentTime - lastPidUpdate >= PID_INTERVAL) {
    handleAutomaticControl(currentTime);
    lastPidUpdate = currentTime;
  }

  // Small delay to prevent overwhelming the serial buffer
  delay(10);
}

/**
 * Process incoming JSON commands from serial port
 */
void processSerialCommands() {
  if (Serial.available()) {
    String message = Serial.readStringUntil('\n');
    message.trim();

    if (message.length() > 0) {
      parseAndExecuteCommand(message);
    }
  }
}

/**
 * Parse JSON command and execute appropriate action
 */
void parseAndExecuteCommand(String message) {
  DeserializationError error = deserializeJson(jsonDoc, message);

  if (error) {
    sendErrorMessage("Invalid JSON: " + String(error.c_str()));
    return;
  }

  // Handle setpoint command
  if (jsonDoc.containsKey("setpoint_c")) {
    float newSetpoint = jsonDoc["setpoint_c"];
    if (newSetpoint >= 0 && newSetpoint <= MAX_TEMP_C) {
      setpointC = newSetpoint;
      sendAckMessage("setpoint_c", newSetpoint);
    } else {
      sendErrorMessage("Setpoint out of range: " + String(newSetpoint));
    }
  }

  // Handle meat setpoint command
  if (jsonDoc.containsKey("meat_setpoint_c")) {
    float newMeatSetpoint = jsonDoc["meat_setpoint_c"];
    if (newMeatSetpoint >= 0 && newMeatSetpoint <= MAX_TEMP_C) {
      meatSetpointC = newMeatSetpoint;
      sendAckMessage("meat_setpoint_c", newMeatSetpoint);
    } else {
      sendErrorMessage("Meat setpoint out of range: " + String(newMeatSetpoint));
    }
  }

  // Handle damper command
  if (jsonDoc.containsKey("damper_percent")) {
    int newDamper = jsonDoc["damper_percent"];
    if (newDamper >= 0 && newDamper <= 100) {
      damperPercent = newDamper;
      setDamperPosition(damperPercent);
      sendAckMessage("damper_percent", newDamper);
    } else {
      sendErrorMessage("Damper percent out of range: " + String(newDamper));
    }
  }

  // Handle PID gains command
  if (jsonDoc.containsKey("pid_gains")) {
    JsonArray gains = jsonDoc["pid_gains"];
    if (gains.size() == 3) {
      pidGains[0] = gains[0]; // P
      pidGains[1] = gains[1]; // I
      pidGains[2] = gains[2]; // D
      pidController.set_gains(pidGains[0], pidGains[1], pidGains[2]);
      sendAckMessage("pid_gains", "updated");
    } else {
      sendErrorMessage("PID gains must be array of 3 values");
    }
  }
  
  // Handle control mode command
  if (jsonDoc.containsKey("control_mode")) {
    String mode = jsonDoc["control_mode"];
    if (mode == "manual") {
      manualControl = true;
      pidController.reset(); // Reset PID state when switching to manual
      sendAckMessage("control_mode", "manual");
    } else if (mode == "automatic") {
      manualControl = false;
      pidController.reset(); // Reset PID state when switching to automatic
      sendAckMessage("control_mode", "automatic");
    } else {
      sendErrorMessage("Invalid control mode: " + mode + " (use 'manual' or 'automatic')");
    }
  }
}

/**
 * Set servo position based on damper percentage
 */
void setDamperPosition(int percent) {
  percent = constrain(percent, 0, 100);
  int servoAngle = map(percent, 0, 100, SERVO_MIN_ANGLE, SERVO_MAX_ANGLE);
  damperServo.write(servoAngle);
}

/**
 * Read temperatures and send status to serial port
 */
void sendTemperatureStatus() {
  // Read temperatures
  float pitTempC = pitThermistor.readTemperatureC();
  float meatTempC = meatThermistor.readTemperatureC();

  // Create JSON response
  jsonDoc.clear();

  // Always include pit temperature
  if (!isnan(pitTempC)) {
    jsonDoc["pit_temp_c"] = round(pitTempC * 100) / 100.0; // Round to 2 decimals
  } else {
    jsonDoc["pit_temp_c"] = nullptr; // Will be sent as null
  }

  // Include meat temperature if valid (probe may be optional)
  if (!isnan(meatTempC)) {
    jsonDoc["meat_temp_c"] = round(meatTempC * 100) / 100.0;
  } else {
    jsonDoc["meat_temp_c"] = nullptr;
  }

  // Include current settings for confirmation
  jsonDoc["setpoint_c"] = setpointC;
  jsonDoc["meat_setpoint_c"] = meatSetpointC;
  jsonDoc["damper_percent"] = damperPercent;
  
  // Include control mode information
  jsonDoc["control_mode"] = manualControl ? "manual" : "automatic";
  if (!manualControl && pidController.is_ready()) {
    jsonDoc["pid_status"]["error"] = pidController.get_last_error();
    jsonDoc["pid_status"]["output"] = pidController.get_last_output();
    jsonDoc["pid_status"]["integral"] = pidController.get_integral_term();
  }

  // Send JSON message
  serializeJson(jsonDoc, jsonBuffer, JSON_BUFFER_SIZE);
  Serial.println(jsonBuffer);
}

/**
 * Send acknowledgment message for received command
 */
void sendAckMessage(String command, float value) {
  jsonDoc.clear();
  jsonDoc["ack"] = command;
  jsonDoc["value"] = value;
  serializeJson(jsonDoc, jsonBuffer, JSON_BUFFER_SIZE);
  Serial.println(jsonBuffer);
}

/**
 * Send acknowledgment message for received command (string version)
 */
void sendAckMessage(String command, String value) {
  jsonDoc.clear();
  jsonDoc["ack"] = command;
  jsonDoc["value"] = value;
  serializeJson(jsonDoc, jsonBuffer, JSON_BUFFER_SIZE);
  Serial.println(jsonBuffer);
}

/**
 * Send error message
 */
void sendErrorMessage(String error) {
  jsonDoc.clear();
  jsonDoc["error"] = error;
  serializeJson(jsonDoc, jsonBuffer, JSON_BUFFER_SIZE);
  Serial.println(jsonBuffer);
}

/**
 * Send diagnostic information (can be called via serial command)
 */
void sendDiagnostics() {
  jsonDoc.clear();
  jsonDoc["diagnostics"]["pit_adc"] = pitThermistor.readRawADC();
  jsonDoc["diagnostics"]["meat_adc"] = meatThermistor.readRawADC();
  jsonDoc["diagnostics"]["servo_angle"] = map(damperPercent, 0, 100, SERVO_MIN_ANGLE, SERVO_MAX_ANGLE);
  jsonDoc["diagnostics"]["free_ram"] = freeRam();
  serializeJson(jsonDoc, jsonBuffer, JSON_BUFFER_SIZE);
  Serial.println(jsonBuffer);
}

/**
 * Handle automatic PID control
 * Updates damper position based on PID controller output
 */
void handleAutomaticControl(unsigned long currentTime) {
  // Get current pit temperature
  float currentTemp = pitThermistor.readTemperatureC();
  
  if (isnan(currentTemp)) {
    // Can't control without valid temperature reading
    return;
  }
  
  // Compute PID output (damper percentage 0-100)
  float pidOutput = pidController.compute(setpointC, currentTemp, currentTime);
  
  // Update damper position
  int newDamperPercent = (int)round(pidOutput);
  if (newDamperPercent != damperPercent) {
    damperPercent = newDamperPercent;
    setDamperPosition(damperPercent);
    
    // Send status update about automatic adjustment
    jsonDoc.clear();
    jsonDoc["pid_update"]["current_temp"] = round(currentTemp * 100) / 100.0;
    jsonDoc["pid_update"]["setpoint"] = setpointC;
    jsonDoc["pid_update"]["error"] = pidController.get_last_error();
    jsonDoc["pid_update"]["output"] = pidOutput;
    jsonDoc["pid_update"]["damper_percent"] = damperPercent;
    
    serializeJson(jsonDoc, jsonBuffer, JSON_BUFFER_SIZE);
    Serial.println(jsonBuffer);
  }
}

/**
 * Get free RAM for diagnostics
 */
int freeRam() {
  extern int __heap_start, *__brkval;
  int v;
  return (int) &v - (__brkval == 0 ? (int) &__heap_start : (int) __brkval);
}
