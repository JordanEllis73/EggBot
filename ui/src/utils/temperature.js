/**
 * Temperature conversion utilities
 */

// Convert Celsius to Fahrenheit
export const celsiusToFahrenheit = (celsius) => {
  if (celsius === null || celsius === undefined) return celsius;
  return (celsius * 9/5) + 32;
};

// Convert Fahrenheit to Celsius
export const fahrenheitToCelsius = (fahrenheit) => {
  if (fahrenheit === null || fahrenheit === undefined) return fahrenheit;
  return (fahrenheit - 32) * 5/9;
};

// Format temperature with unit symbol
export const formatTemperature = (temp, unit = 'C', decimals = 1) => {
  if (temp === null || temp === undefined) return '—';
  
  const symbol = unit === 'F' ? '°F' : '°C';
  return `${temp.toFixed(decimals)}${symbol}`;
};

// Convert temperature based on unit preference
export const convertTemperature = (temp, fromUnit, toUnit) => {
  if (temp === null || temp === undefined) return temp;
  if (fromUnit === toUnit) return temp;
  
  if (fromUnit === 'C' && toUnit === 'F') {
    return celsiusToFahrenheit(temp);
  } else if (fromUnit === 'F' && toUnit === 'C') {
    return fahrenheitToCelsius(temp);
  }
  
  return temp;
};

// Get display temperature (API uses Celsius, convert if needed)
export const getDisplayTemperature = (tempC, unit) => {
  return unit === 'F' ? celsiusToFahrenheit(tempC) : tempC;
};

// Get API temperature (convert to Celsius if needed)
export const getApiTemperature = (displayTemp, unit) => {
  return unit === 'F' ? fahrenheitToCelsius(displayTemp) : displayTemp;
};