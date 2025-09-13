#ifndef THERMISTOR_H
#define THERMISTOR_H

#include "Arduino.h"
#include "config.h"

/**
 * Thermistor class for accurate temperature measurement using Steinhart-Hart equation
 */
class Thermistor {
  private:
    int pin;
    float aCoeff, bCoeff, cCoeff;
    int refResistor;
    int samples;
    
  public:
    /**
     * Constructor
     * @param analogPin - Arduino analog pin connected to thermistor
     * @param a, b, c - Steinhart-Hart coefficients
     * @param referenceResistor - Value of reference resistor in voltage divider
     * @param numSamples - Number of ADC readings to average
     */
    Thermistor(int analogPin, 
               float a = A_COEFF, 
               float b = B_COEFF, 
               float c = C_COEFF, 
               int referenceResistor = REFERENCE_RESISTOR,
               int numSamples = ADC_SAMPLES);
    
    /**
     * Read temperature in Celsius using Steinhart-Hart equation
     * @return Temperature in Celsius, or NaN if reading is invalid
     */
    float readTemperatureC();
    
    /**
     * Read temperature in Fahrenheit
     * @return Temperature in Fahrenheit, or NaN if reading is invalid
     */
    float readTemperatureF();
    
    /**
     * Read raw ADC value (averaged)
     * @return Raw ADC value (0-1023)
     */
    int readRawADC();
    
    /**
     * Calculate resistance from ADC reading
     * @param adcValue - Raw ADC reading
     * @return Thermistor resistance in ohms
     */
    float calculateResistance(int adcValue);
    
    /**
     * Validate temperature reading
     * @param tempC - Temperature in Celsius
     * @return true if temperature is within reasonable range
     */
    bool isValidTemperature(float tempC);
    
    /**
     * Update Steinhart-Hart coefficients for calibration
     * @param a, b, c - New coefficients
     */
    void setCoefficients(float a, float b, float c);
};

#endif // THERMISTOR_H