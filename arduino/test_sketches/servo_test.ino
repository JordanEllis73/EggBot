/**
 * Servo Test Sketch
 *
 * This simple sketch tests servo movement for the damper control.
 * Use this to verify servo wiring and calibrate servo angles before
 * using the main controller sketch.
 *
 * Wiring:
 * - Servo signal wire (orange/yellow) to pin 9
 * - Servo power wire (red) to 5V
 * - Servo ground wire (brown/black) to GND
 *
 * Serial Monitor Commands:
 * - Send numbers 0-100 to set damper percentage
 * - Send "sweep" to run automatic sweep test
 */

#include <Servo.h>

// Configuration
const int SERVO_PIN = 9;
const int MIN_ANGLE = 0;   // Servo angle for 0% damper (closed)
const int MAX_ANGLE = 90;  // Servo angle for 100% damper (open)

Servo damperServo;
int currentPercent = 0;

void setup() {
  Serial.begin(115200);
  Serial.println("Servo Test - EggBot Damper Control");
  Serial.println("Commands:");
  Serial.println("  0-100: Set damper percentage");
  Serial.println("  sweep: Run automatic sweep test");
  Serial.println("  help: Show this help");
  Serial.println();

  // Attach servo
  damperServo.attach(SERVO_PIN);
  setDamperPercent(0);  // Start closed

  Serial.println("Servo attached to pin " + String(SERVO_PIN));
  Serial.println("Current position: 0% (closed)");
  Serial.println();
}

void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "sweep") {
      runSweepTest();
    } else if (command == "help") {
      showHelp();
    } else {
      // Try to parse as percentage
      int percent = command.toInt();
      if (percent >= 0 && percent <= 100) {
        setDamperPercent(percent);
      } else if (command.length() > 0) {
        Serial.println("Invalid command: " + command);
        Serial.println("Use 0-100 for percentage, 'sweep' for test, or 'help'");
      }
    }
  }
}

void setDamperPercent(int percent) {
  percent = constrain(percent, 0, 100);
  currentPercent = percent;

  int servoAngle = map(percent, 0, 100, MIN_ANGLE, MAX_ANGLE);
  damperServo.write(servoAngle);

  Serial.println("Damper set to " + String(percent) +
                 "% (servo angle: " + String(servoAngle) + "°)");

  if (percent == 0) {
    Serial.println("  → Damper CLOSED");
  } else if (percent == 100) {
    Serial.println("  → Damper FULLY OPEN");
  } else if (percent < 25) {
    Serial.println("  → Damper mostly closed");
  } else if (percent < 75) {
    Serial.println("  → Damper partially open");
  } else {
    Serial.println("  → Damper mostly open");
  }
}

void runSweepTest() {
  Serial.println("Starting sweep test...");
  Serial.println("This will move the damper from 0% to 100% and back");

  // Sweep from 0 to 100
  Serial.println("Sweeping UP (0% → 100%):");
  for (int percent = 0; percent <= 100; percent += 10) {
    setDamperPercent(percent);
    delay(500);
  }

  delay(1000);

  // Sweep from 100 to 0
  Serial.println("Sweeping DOWN (100% → 0%):");
  for (int percent = 100; percent >= 0; percent -= 10) {
    setDamperPercent(percent);
    delay(500);
  }

  Serial.println("Sweep test complete!");
  Serial.println("Current position: 0% (closed)");
  Serial.println();
}

void showHelp() {
  Serial.println();
  Serial.println("=== EggBot Servo Test Help ===");
  Serial.println("Commands:");
  Serial.println("  0-100    Set damper percentage");
  Serial.println("           Example: 50 (sets damper to 50%)");
  Serial.println("  sweep    Run automatic sweep test");
  Serial.println("           Moves from 0% to 100% and back");
  Serial.println("  help     Show this help message");
  Serial.println();
  Serial.println("Hardware Setup:");
  Serial.println("  Servo signal → Pin " + String(SERVO_PIN));
  Serial.println("  Servo power  → 5V");
  Serial.println("  Servo ground → GND");
  Serial.println();
  Serial.println("Configuration:");
  Serial.println("  Closed angle (0%):  " + String(MIN_ANGLE) + "°");
  Serial.println("  Open angle (100%):  " + String(MAX_ANGLE) + "°");
  Serial.println("  Current position:   " + String(currentPercent) + "%");
  Serial.println();
}