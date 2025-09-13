/**
 * Thermistor Test Sketch
 *
 * This simple sketch tests thermistor readings without the full EggBot
 * protocol. Use this to verify your thermistor wiring and calibration before
 * using the main controller sketch.
 *
 * Wiring:
 * - Thermistor between A0 and GND
 * - 10kΩ resistor between A0 and 5V
 *
 * Serial Monitor Output:
 * - ADC reading (0-1023)
 * - Calculated resistance
 * - Temperature in Celsius and Fahrenheit
 */

// Configuration
const int THERMISTOR_PIN = A0;
const int REFERENCE_RESISTOR = 10000;  // 10kΩ

// Steinhart-Hart coefficients for typical 10kΩ NTC thermistor
const float A_COEFF = 0.0007343140544;
const float B_COEFF = 0.0002157437229;
const float C_COEFF = 0.0000000951568577;

void setup() {
  Serial.begin(115200);
  Serial.println("Thermistor Test - Starting in 3 seconds...");
  delay(3000);

  Serial.println("ADC\tResistance\tTemp(C)\tTemp(F)");
  Serial.println("---\t----------\t-------\t-------");
}

void loop() {
  // Read ADC value (average of multiple readings)
  long adcSum = 0;
  const int samples = 10;

  for (int i = 0; i < samples; i++) {
    adcSum += analogRead(THERMISTOR_PIN);
    delay(10);
  }

  int adcValue = adcSum / samples;

  // Calculate thermistor resistance
  if (adcValue <= 0 || adcValue >= 1023) {
    Serial.println("Invalid ADC reading!");
    delay(1000);
    return;
  }

  float resistance =
      REFERENCE_RESISTOR * ((float)adcValue / (1023.0 - (float)adcValue));

  // Calculate temperature using Steinhart-Hart equation
  float logR = log(resistance);
  float logR3 = logR * logR * logR;
  float tempK = 1.0 / (A_COEFF + (B_COEFF * logR) + (C_COEFF * logR3));
  float tempC = tempK - 273.15;
  float tempF = (tempC * 9.0 / 5.0) + 32.0;

  // Output results
  Serial.print(adcValue);
  Serial.print("\t");
  Serial.print(resistance, 1);
  Serial.print("\t\t");
  Serial.print(tempC, 2);
  Serial.print("\t");
  Serial.print(tempF, 2);
  Serial.println();

  delay(1000);  // Update every second
}
