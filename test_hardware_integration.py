#!/usr/bin/env python3
"""
Hardware integration test script for Pi-native EggBot
Tests ADS1115 ADC, thermistor calculations, and servo control
"""

import sys
import time
import logging
from typing import Dict, Optional

# Add pi_native to path
sys.path.insert(0, '.')

from pi_native.hardware.ads1115_manager import ADS1115Manager
from pi_native.hardware.thermistor_calc import ThermistorCalculator
from pi_native.hardware.servo_controller import ServoController
from pi_native.config.hardware import hardware_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_adc_readings():
    """Test ADS1115 ADC functionality"""
    print("\n=== Testing ADS1115 ADC ===")
    
    try:
        adc = ADS1115Manager(simulate=False)  # Try real hardware first
        if adc.simulate:
            print("Running in SIMULATION mode (hardware not available)")
        else:
            print("Connected to real ADS1115 hardware")
        
        # Test reading all channels
        print("\nReading all channels:")
        readings = adc.read_all_channels()
        
        for channel, reading in readings.items():
            print(f"Channel {channel}: {reading.voltage:.3f}V (raw: {reading.raw_value})")
        
        # Test connected channel detection
        connected = adc.get_connected_channels()
        print(f"\nConnected channels: {connected}")
        
        adc.close()
        return True
        
    except Exception as e:
        logger.error(f"ADC test failed: {e}")
        return False

def test_thermistor_calculations():
    """Test thermistor temperature calculations"""
    print("\n=== Testing Thermistor Calculations ===")
    
    try:
        calc = ThermistorCalculator()
        
        # Test voltage to temperature conversion for different voltages
        test_voltages = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
        
        print("\nVoltage to Temperature conversions:")
        print("Voltage (V) | Temp (°C) | Temp (°F)")
        print("-" * 35)
        
        for voltage in test_voltages:
            temp_c = calc.voltage_to_temperature(voltage, channel=0)
            if temp_c:
                temp_f = temp_c * 9/5 + 32
                print(f"{voltage:8.1f} | {temp_c:7.1f} | {temp_f:7.1f}")
        
        # Test calibration
        print(f"\nTesting calibration on channel 0...")
        calc.calibrate_probe(0, measured_temp=25.0, actual_temp=26.5)
        
        # Test range calculation
        config = calc.get_probe_config(0)
        temp_range = calc.get_temperature_range(config)
        print(f"Temperature range for channel 0: {temp_range[0]:.1f}°C to {temp_range[1]:.1f}°C")
        
        return True
        
    except Exception as e:
        logger.error(f"Thermistor test failed: {e}")
        return False

def test_servo_control():
    """Test servo controller functionality"""
    print("\n=== Testing Servo Control ===")
    
    try:
        servo = ServoController(gpio_pin=18, simulate=False)
        if servo.simulate:
            print("Running in SIMULATION mode (pigpio not available)")
        else:
            print("Connected to real servo hardware")
        
        print(f"Initial position: {servo.get_position_percent():.1f}%")
        
        # Test basic positioning
        positions = [0, 25, 50, 75, 100, 50]
        
        for pos in positions:
            print(f"Moving to {pos}%...")
            servo.set_position_percent(pos)
            
            # Wait for movement to complete
            start_time = time.time()
            while not servo.is_at_target() and (time.time() - start_time) < 5.0:
                current = servo.get_position_percent()
                pulse = servo.get_pulse_width()
                print(f"  Current: {current:.1f}% (pulse: {pulse}μs)")
                time.sleep(0.5)
            
            print(f"  Reached: {servo.get_position_percent():.1f}%")
        
        servo.close()
        return True
        
    except Exception as e:
        logger.error(f"Servo test failed: {e}")
        return False

def test_integrated_system():
    """Test complete system integration"""
    print("\n=== Testing Integrated System ===")
    
    try:
        # Initialize all components
        adc = ADS1115Manager()
        calc = ThermistorCalculator()
        servo = ServoController()
        
        print("All hardware components initialized")
        
        # Simulate a control loop
        print("\nSimulating control loop for 10 seconds...")
        
        for i in range(10):
            # Read temperatures
            readings = adc.read_all_channels()
            temperatures: Dict[str, Optional[float]] = {}
            
            for channel, reading in readings.items():
                temp = calc.voltage_to_temperature(reading.voltage, channel)
                probe_name = hardware_config.PROBE_CHANNEL_MAP[channel]
                temperatures[probe_name] = temp
            
            # Display current status
            pit_temp = temperatures.get("pit_probe")
            meat_temp = temperatures.get("meat_probe_1")
            servo_pos = servo.get_position_percent()
            
            print(f"Cycle {i+1}: Pit={pit_temp:.1f}°C, Meat={meat_temp:.1f}°C, Damper={servo_pos:.1f}%")
            
            # Simple control logic (demo)
            if pit_temp and pit_temp < 100:
                servo.set_position_percent(min(100, servo_pos + 10))
            elif pit_temp and pit_temp > 120:
                servo.set_position_percent(max(0, servo_pos - 10))
            
            time.sleep(1)
        
        # Cleanup
        adc.close()
        servo.close()
        
        print("Integration test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        return False

def main():
    """Run all hardware tests"""
    print("Pi-Native EggBot Hardware Integration Test")
    print("=" * 45)
    
    tests = [
        ("ADC Readings", test_adc_readings),
        ("Thermistor Calculations", test_thermistor_calculations), 
        ("Servo Control", test_servo_control),
        ("Integrated System", test_integrated_system)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\nRunning {test_name}...")
        try:
            success = test_func()
            results.append((test_name, success))
        except KeyboardInterrupt:
            print("\nTest interrupted by user")
            break
        except Exception as e:
            logger.error(f"Unexpected error in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 45)
    print("TEST SUMMARY:")
    print("=" * 45)
    
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{test_name:<25}: {status}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("All tests passed! Hardware layer ready for integration.")
        return 0
    else:
        print("Some tests failed. Check logs and hardware connections.")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nTest suite interrupted")
        sys.exit(130)