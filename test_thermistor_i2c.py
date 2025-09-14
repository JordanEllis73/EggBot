#!/usr/bin/env python3
"""
Thermistor I2C Test Script for Raspberry Pi
Tests the 4 temperature probe circuits connected via ADS1115

Run this on the Raspberry Pi to verify thermistor readings.
"""

import time
import sys
import os

# Add pi_native to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pi_native'))

try:
    from pi_native.hardware.ads1115_manager import ADS1115Manager
    from pi_native.hardware.thermistor_calc import ThermistorCalculator
    from pi_native.config.hardware import hardware_config, PROBE_CHANNEL_MAP
except ImportError as e:
    print(f"Error importing pi_native modules: {e}")
    print("Make sure you're running this on the Raspberry Pi with dependencies installed")
    sys.exit(1)

def test_thermistor_readings():
    """Test thermistor readings from all 4 channels"""
    print("=" * 60)
    print("Thermistor I2C Test Script")
    print("=" * 60)
    print("Testing 4 temperature probes via ADS1115 I2C interface")
    print(f"I2C Address: 0x{hardware_config.adc.i2c_address:02x}")
    print("Channels: 0=Pit, 1=Meat1, 2=Meat2, 3=Ambient")
    print("-" * 60)
    
    try:
        # Initialize ADS1115 manager
        print("Initializing ADS1115...")
        adc_manager = ADS1115Manager(
            i2c_address=hardware_config.adc.i2c_address,
            simulate=False
        )
        print("✓ ADS1115 initialized successfully")
        
        # Initialize thermistor calculators for each probe
        calculators = {}
        for channel, probe_name in PROBE_CHANNEL_MAP.items():
            config = hardware_config.get_probe_config(channel)
            calculators[probe_name] = ThermistorCalculator(config)
        print("✓ Thermistor calculators initialized")
        
        print("\nStarting temperature readings (Press Ctrl+C to stop)...")
        print("-" * 60)
        
        while True:
            print(f"\n[{time.strftime('%H:%M:%S')}] Temperature Readings:")
            
            for channel in range(4):
                probe_name = PROBE_CHANNEL_MAP.get(channel, f"Channel_{channel}")
                
                try:
                    # Read raw voltage from ADC
                    reading = adc_manager.read_channel(channel)
                    
                    if reading and reading.voltage is not None:
                        # Calculate temperature using thermistor calculator
                        calculator = calculators.get(probe_name)
                        if calculator:
                            temp_c = calculator.voltage_to_temperature(reading.voltage)
                            temp_f = temp_c * 9/5 + 32 if temp_c is not None else None
                            
                            print(f"  Ch{channel} ({probe_name:12}): {reading.voltage:.3f}V -> "
                                  f"{temp_c:.1f}°C ({temp_f:.1f}°F)" if temp_c else 
                                  f"  Ch{channel} ({probe_name:12}): {reading.voltage:.3f}V -> ERROR")
                        else:
                            print(f"  Ch{channel} ({probe_name:12}): {reading.voltage:.3f}V -> No calculator")
                    else:
                        print(f"  Ch{channel} ({probe_name:12}): ERROR - No reading")
                        
                except Exception as e:
                    print(f"  Ch{channel} ({probe_name:12}): ERROR - {e}")
            
            print("-" * 60)
            time.sleep(2)  # Update every 2 seconds
            
    except KeyboardInterrupt:
        print("\n\nTest stopped by user")
    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nTroubleshooting:")
        print("1. Check I2C is enabled: sudo raspi-config -> Interface Options -> I2C")
        print("2. Check ADS1115 connection: sudo i2cdetect -y 1")
        print("3. Verify wiring: SDA=GPIO2, SCL=GPIO3, VDD=3.3V, GND=GND")
        print("4. Check thermistor connections to ADS1115 channels 0-3")
        return False
    finally:
        print("Cleaning up...")
        try:
            if 'adc_manager' in locals():
                adc_manager.close()
        except:
            pass
    
    return True

def check_i2c_setup():
    """Check if I2C and ADS1115 are properly configured"""
    print("Checking I2C setup...")
    
    try:
        # Try to run i2cdetect to see if ADS1115 is visible
        import subprocess
        result = subprocess.run(['i2cdetect', '-y', '1'], 
                              capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            print("✓ I2C bus accessible")
            if '48' in result.stdout:
                print("✓ ADS1115 detected at address 0x48")
                return True
            else:
                print("⚠ ADS1115 not detected at 0x48")
                print("Available I2C devices:")
                print(result.stdout)
                return False
        else:
            print("⚠ I2C bus not accessible")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠ I2C detection timed out")
        return False
    except FileNotFoundError:
        print("⚠ i2cdetect command not found (install i2c-tools)")
        return False
    except Exception as e:
        print(f"⚠ I2C check failed: {e}")
        return False

def main():
    print("Raspberry Pi Thermistor I2C Test")
    print("================================")
    
    # Check I2C setup first
    if not check_i2c_setup():
        print("\nI2C setup issues detected. Please resolve before running test.")
        return 1
    
    # Run thermistor test
    success = test_thermistor_readings()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())