#!/usr/bin/env python3
"""
Debug Thermistor Calculations
Helps diagnose temperature reading issues by showing intermediate values
"""

import time
import sys
import os
import math

# Add pi_native to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pi_native'))

try:
    from pi_native.hardware.ads1115_manager import ADS1115Manager
    from pi_native.hardware.thermistor_calc import ThermistorCalculator, ThermistorConfig, SteinhartHartCoefficients
    from pi_native.config.hardware import hardware_config, PROBE_CHANNEL_MAP
except ImportError as e:
    print(f"Error importing pi_native modules: {e}")
    sys.exit(1)

def debug_thermistor_calculation(voltage, channel=0):
    """Debug a single thermistor calculation showing all intermediate steps"""
    print(f"\n=== Debug Calculation for Channel {channel} ===")
    print(f"Input voltage: {voltage:.3f}V")
    
    # Get configuration
    calculator = ThermistorCalculator(supply_voltage=hardware_config.adc.supply_voltage)
    config = hardware_config.get_probe_config(channel)
    calculator.set_probe_config(channel, config)
    
    print(f"Supply voltage: {calculator.supply_voltage:.3f}V")
    print(f"Series resistor: {config.series_resistor}Ω")
    print(f"Nominal resistance: {config.resistance_nominal}Ω at {config.temperature_nominal}°C")
    print(f"B coefficient: {config.b_coefficient}")
    
    try:
        # Step 1: Convert voltage to resistance
        resistance = calculator.voltage_to_resistance(voltage, config.series_resistor)
        print(f"Calculated resistance: {resistance:.0f}Ω")
        
        # Step 2: Try Beta equation
        temp_beta = calculator.resistance_to_temperature_beta(resistance, config)
        print(f"Beta equation temperature: {temp_beta:.1f}°C ({temp_beta * 9/5 + 32:.1f}°F)")
        
        # Step 3: Try Steinhart-Hart equation
        if config.steinhart_hart:
            temp_sh = calculator.resistance_to_temperature_steinhart_hart(resistance, config)
            print(f"Steinhart-Hart temperature: {temp_sh:.1f}°C ({temp_sh * 9/5 + 32:.1f}°F)")
            
            # Show Steinhart-Hart calculation details
            coeff = config.steinhart_hart
            print(f"Steinhart-Hart coefficients: A={coeff.A}, B={coeff.B}, C={coeff.C}")
            ln_r = math.log(resistance)
            temp_kelvin_inv = coeff.A + coeff.B * ln_r + coeff.C * (ln_r ** 3)
            temp_kelvin = 1.0 / temp_kelvin_inv
            print(f"ln(R) = {ln_r:.6f}")
            print(f"1/T = {temp_kelvin_inv:.9f}")
            print(f"T = {temp_kelvin:.2f}K = {temp_kelvin - 273.15:.1f}°C")
        
        # Step 4: What should the resistance be for room temp?
        room_temp_c = 21.0  # ~70°F
        expected_resistance = calculate_expected_resistance(room_temp_c, config)
        expected_voltage = calculate_expected_voltage(expected_resistance, config.series_resistor, calculator.supply_voltage)
        print(f"\nFor {room_temp_c}°C ({room_temp_c * 9/5 + 32:.1f}°F):")
        print(f"Expected resistance: {expected_resistance:.0f}Ω")
        print(f"Expected voltage: {expected_voltage:.3f}V")
        
    except Exception as e:
        print(f"Calculation error: {e}")

def calculate_expected_resistance(temp_c, config):
    """Calculate expected resistance for a given temperature using Beta equation"""
    t_kelvin = temp_c + 273.15
    t0_kelvin = config.temperature_nominal + 273.15
    
    # Beta equation: R = R0 * exp(B * (1/T - 1/T0))
    resistance = config.resistance_nominal * math.exp(config.b_coefficient * (1/t_kelvin - 1/t0_kelvin))
    return resistance

def calculate_expected_voltage(resistance, series_resistor, supply_voltage):
    """Calculate expected voltage for a given resistance"""
    # Assuming thermistor is on bottom of voltage divider
    # V_out = V_supply * R_thermistor / (R_series + R_thermistor)
    voltage = supply_voltage * resistance / (series_resistor + resistance)
    return voltage

def test_different_coefficients():
    """Test with different Steinhart-Hart coefficients for common thermistors"""
    print("\n=== Testing Different Thermistor Types ===")
    
    # Common Steinhart-Hart coefficients for different thermistors
    thermistor_types = {
        "Generic 10K NTC": SteinhartHartCoefficients(
            A=0.001129148, B=0.000234125, C=0.0000000876741
        ),
        "Vishay NTCLE100E3": SteinhartHartCoefficients(
            A=0.001125308852122, B=0.000234711863267, C=0.000000085663516
        ),
        "Epcos B57164K": SteinhartHartCoefficients(
            A=0.003354016, B=0.000256985, C=0.000000205154
        ),
        "Murata NCP18XH103": SteinhartHartCoefficients(
            A=0.001129241, B=0.000234126, C=0.0000000876741
        )
    }
    
    # Test with a voltage that should be room temperature
    test_voltage = 1.65  # Adjust this to your actual reading
    
    for name, coeffs in thermistor_types.items():
        config = ThermistorConfig(
            name=name,
            resistance_nominal=10000,
            temperature_nominal=25.0,
            b_coefficient=3950,
            series_resistor=10000,
            steinhart_hart=coeffs,
            offset_c=0.0
        )
        
        calculator = ThermistorCalculator(supply_voltage=3.3)
        try:
            resistance = calculator.voltage_to_resistance(test_voltage, config.series_resistor)
            temp = calculator.resistance_to_temperature_steinhart_hart(resistance, config)
            print(f"{name:20}: {temp:.1f}°C ({temp * 9/5 + 32:.1f}°F)")
        except Exception as e:
            print(f"{name:20}: ERROR - {e}")

def main():
    print("Thermistor Debug Tool")
    print("====================")
    
    # Test with actual readings
    try:
        adc_manager = ADS1115Manager(i2c_address=0x48, simulate=False)
        
        print("\nCurrent ADC readings:")
        for channel in range(4):
            probe_name = PROBE_CHANNEL_MAP.get(channel, f"Channel_{channel}")
            try:
                reading = adc_manager.read_channel(channel)
                if reading:
                    print(f"Ch{channel} ({probe_name}): {reading.voltage:.3f}V")
                    if channel == 0:  # Debug first channel in detail
                        debug_thermistor_calculation(reading.voltage, channel)
                else:
                    print(f"Ch{channel} ({probe_name}): No reading")
            except Exception as e:
                print(f"Ch{channel} ({probe_name}): ERROR - {e}")
        
        adc_manager.close()
        
    except Exception as e:
        print(f"ADC error: {e}")
        print("Testing with simulated voltage...")
        debug_thermistor_calculation(1.65, 0)  # Simulate a reading
    
    # Test different thermistor types
    test_different_coefficients()
    
    print("\n=== Troubleshooting Tips ===")
    print("1. Check if thermistor is connected to top or bottom of voltage divider")
    print("2. Verify thermistor part number and look up correct Steinhart-Hart coefficients")
    print("3. Try the Beta equation if Steinhart-Hart seems wrong")
    print("4. Check if voltage divider equation matches your circuit")
    print("5. Measure actual thermistor resistance with multimeter at room temp")

if __name__ == "__main__":
    main()