#include "thermistor.h"

#include <math.h>

Thermistor::Thermistor(int analogPin, float a, float b, float c,
                       int referenceResistor, int numSamples) {
  pin = analogPin;
  aCoeff = a;
  bCoeff = b;
  cCoeff = c;
  refResistor = referenceResistor;
  samples = numSamples;

  // Set pin mode (though analog pins don't strictly need this)
  pinMode(pin, INPUT);
}

float Thermistor::readTemperatureC() {
  int adcValue = readRawADC();
  if (adcValue <= 0 || adcValue >= 1023) {
    return NAN;  // Invalid reading
  }

  float resistance = calculateResistance(adcValue);
  if (resistance <= 0) {
    return NAN;
  }

  // Steinhart-Hart equation: 1/T = A + B*ln(R) + C*ln(R)^3
  // Where T is in Kelvin and R is resistance
  float logR = log(resistance);
  float logR3 = logR * logR * logR;

  float tempK = 1.0 / (aCoeff + (bCoeff * logR) + (cCoeff * logR3));
  float tempC = tempK - 273.15;  // Convert Kelvin to Celsius

  if (!isValidTemperature(tempC)) {
    return NAN;
  }

  return tempC;
}

float Thermistor::readTemperatureF() {
  float tempC = readTemperatureC();
  if (isnan(tempC)) {
    return NAN;
  }
  return (tempC * 9.0 / 5.0) + 32.0;
}

int Thermistor::readRawADC() {
  long sum = 0;
  int validReadings = 0;

  for (int i = 0; i < samples; i++) {
    int reading = analogRead(pin);
    if (reading >= 0 && reading <= 1023) {
      sum += reading;
      validReadings++;
    }
    if (i < samples - 1) {
      delay(5);  // Small delay between readings
    }
  }

  if (validReadings == 0) {
    return -1;  // No valid readings
  }

  return sum / validReadings;
}

float Thermistor::calculateResistance(int adcValue) {
  if (adcValue <= 0 || adcValue >= 1023) {
    return -1.0;
  }

  // Standard voltage divider with thermistor as R2 (lower resistor)
  // Circuit: 5V -> R1 (reference) -> ADC_PIN -> R2 (thermistor) -> GND
  // For NTC thermistors: higher temperature = lower resistance = higher ADC
  // reading
  //
  // Voltage divider equation: Vout = Vin * (R2 / (R1 + R2))
  // Solving for R2: R2 = R1 * (Vout / (Vin - Vout))
  // With 10-bit ADC: R2 = R1 * (ADC / (1023 - ADC))

  float adcFloat = (float)adcValue;
  float resistance = refResistor * (1023.0 / adcFloat - 1.0);

  // Validate resistance range for typical NTC thermistors
  // At room temp (~25°C): ~10kΩ
  // At cooking temps (100-300°C): ~100Ω to 2kΩ
  if (resistance < 10.0 || resistance > 300000.0) {
    return -1.0;  // Likely a wiring issue or sensor failure
  }

  return resistance;
}

bool Thermistor::isValidTemperature(float tempC) {
  return (tempC >= MIN_TEMP_C && tempC <= MAX_TEMP_C);
}

void Thermistor::setCoefficients(float a, float b, float c) {
  aCoeff = a;
  bCoeff = b;
  cCoeff = c;
}
