/**
 * NTC Thermistor Resistance Calculator
 *
 * This sketch helps you understand the relationship between ADC readings,
 * resistance values, and temperatures for NTC thermistors.
 *
 * Enter ADC values via Serial Monitor to see calculated resistance and
 * temperature. Useful for calibrating your thermistor setup and troubleshooting
 * readings.
 *
 * Usage:
 * 1. Upload sketch to Arduino
 * 2. Open Serial Monitor (115200 baud)
 * 3. Enter ADC values (0-1023) to see calculations
 * 4. Enter "table" to see a complete lookup table
 */

// Configuration - match your hardware setup
const int REFERENCE_RESISTOR = 10000;  // 10kΩ reference resistor
const float VCC = 5.0;                 // Arduino supply voltage

// Steinhart-Hart coefficients for NTC thermistor
const float A_COEFF = 0.0007343140544;
const float B_COEFF = 0.0002157437229;
const float C_COEFF = 0.0000000951568577;

void setup() {
  Serial.begin(115200);
  Serial.println("=== NTC Thermistor Calculator ===");
  Serial.println("Enter ADC value (0-1023) or 'table' for lookup table");
  Serial.println("Reference resistor: " + String(REFERENCE_RESISTOR) + " ohms");
  Serial.println("Supply voltage: " + String(VCC) + "V");
  Serial.println();
}

void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    if (input == "table") {
      printLookupTable();
    } else if (input == "help") {
      printHelp();
    } else {
      int adcValue = input.toInt();
      if (adcValue >= 0 && adcValue <= 1023) {
        calculateAndPrint(adcValue);
      } else if (input.length() > 0) {
        Serial.println("Invalid input: " + input);
        Serial.println("Enter ADC value (0-1023), 'table', or 'help'");
      }
    }
  }
}

void calculateAndPrint(int adcValue) {
  Serial.println("--- ADC Value: " + String(adcValue) + " ---");

  // Calculate voltage at ADC pin
  float voltage = (adcValue / 1023.0) * VCC;
  Serial.println("Voltage: " + String(voltage, 3) + "V");

  // Calculate thermistor resistance
  if (adcValue <= 0) {
    Serial.println("Resistance: INFINITE (open circuit)");
    Serial.println("Temperature: N/A");
    return;
  } else if (adcValue >= 1023) {
    Serial.println("Resistance: 0 ohms (short circuit)");
    Serial.println("Temperature: N/A");
    return;
  }

  float resistance =
      REFERENCE_RESISTOR * ((float)adcValue / (1023.0 - (float)adcValue));
  Serial.println("Resistance: " + String(resistance, 1) + " ohms");

  // Calculate temperature using Steinhart-Hart
  if (resistance <= 0) {
    Serial.println("Temperature: N/A (invalid resistance)");
    return;
  }

  float logR = log(resistance);
  float logR3 = logR * logR * logR;
  float tempK = 1.0 / (A_COEFF + (B_COEFF * logR) + (C_COEFF * logR3));
  float tempC = tempK - 273.15;
  float tempF = (tempC * 9.0 / 5.0) + 32.0;

  Serial.println("Temperature: " + String(tempC, 2) + "°C (" +
                 String(tempF, 2) + "°F)");

  // Provide interpretation
  if (tempC < -10) {
    Serial.println("→ Very cold or incorrect thermistor type");
  } else if (tempC < 10) {
    Serial.println("→ Cold environment");
  } else if (tempC < 30) {
    Serial.println("→ Room temperature");
  } else if (tempC < 100) {
    Serial.println("→ Warm environment");
  } else if (tempC < 200) {
    Serial.println("→ Low cooking temperature");
  } else if (tempC < 300) {
    Serial.println("→ High cooking temperature");
  } else {
    Serial.println("→ Extremely hot or sensor error");
  }

  Serial.println();
}

void printLookupTable() {
  Serial.println("=== NTC Thermistor Lookup Table ===");
  Serial.println("ADC\tVoltage\tResistance\tTemp(°C)\tTemp(°F)\tDescription");
  Serial.println("---\t-------\t----------\t--------\t--------\t-----------");

  int adcValues[] = {50,  100, 200, 300, 400, 500,
                     600, 700, 800, 900, 950, 1000};
  int numValues = sizeof(adcValues) / sizeof(adcValues[0]);

  for (int i = 0; i < numValues; i++) {
    int adc = adcValues[i];
    float voltage = (adc / 1023.0) * VCC;
    float resistance =
        REFERENCE_RESISTOR * ((float)adc / (1023.0 - (float)adc));

    if (resistance > 0) {
      float logR = log(resistance);
      float logR3 = logR * logR * logR;
      float tempK = 1.0 / (A_COEFF + (B_COEFF * logR) + (C_COEFF * logR3));
      float tempC = tempK - 273.15;
      float tempF = (tempC * 9.0 / 5.0) + 32.0;

      String description;
      if (tempC < 0)
        description = "Very cold";
      else if (tempC < 20)
        description = "Cold";
      else if (tempC < 35)
        description = "Room temp";
      else if (tempC < 100)
        description = "Warm";
      else if (tempC < 200)
        description = "Low cook";
      else if (tempC < 300)
        description = "High cook";
      else
        description = "Very hot";

      Serial.print(String(adc) + "\t");
      Serial.print(String(voltage, 2) + "V\t");
      Serial.print(String(resistance, 0) + "Ω\t\t");
      Serial.print(String(tempC, 1) + "°C\t\t");
      Serial.print(String(tempF, 1) + "°F\t\t");
      Serial.println(description);
    }
  }
  Serial.println();
}

void printHelp() {
  Serial.println("=== NTC Calculator Help ===");
  Serial.println("Commands:");
  Serial.println(
      "  0-1023   Calculate resistance and temperature for ADC value");
  Serial.println("  table    Show complete lookup table");
  Serial.println("  help     Show this help");
  Serial.println();
  Serial.println("Understanding NTC Behavior:");
  Serial.println("• NTC = Negative Temperature Coefficient");
  Serial.println(
      "• Higher temperature = Lower resistance = Higher ADC reading");
  Serial.println("• Room temperature (~25°C) ≈ 10kΩ ≈ ADC 512");
  Serial.println("• Cooking temperature (~200°C) ≈ 200Ω ≈ ADC 950");
  Serial.println();
  Serial.println("Troubleshooting:");
  Serial.println("• ADC near 0: Thermistor disconnected or very cold");
  Serial.println("• ADC near 1023: Thermistor shorted or extremely hot");
  Serial.println("• Unstable readings: Check wiring and connections");
  Serial.println();
}