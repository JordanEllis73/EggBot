#!/usr/bin/env python3
"""
Complete PID system test script for Pi-native EggBot
Tests PID controller, temperature monitoring, and integrated control
"""

import sys
import time
import logging
from typing import Dict, List
import matplotlib.pyplot as plt
import numpy as np

# Add pi_native to path
sys.path.insert(0, '.')

from pi_native.control.pid_controller import PIDController
from pi_native.control.temperature_monitor import TemperatureMonitor
from pi_native.control.eggbot_controller import EggBotController
from pi_native.config.pid import PID_PRESETS, default_control_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_pid_controller():
    """Test PID controller in isolation"""
    print("\n=== Testing PID Controller ===")
    
    try:
        # Test with conservative preset
        config = PID_PRESETS["conservative"]
        pid = PIDController(config)
        
        print(f"PID initialized with gains: {pid.get_gains()}")
        
        # Set a target temperature
        target_temp = 125.0  # °C
        pid.set_setpoint(target_temp)
        
        # Simulate temperature response
        current_temp = 25.0  # Starting temperature
        temps = [current_temp]
        outputs = []
        times = []
        
        print("\nRunning PID simulation for 60 seconds...")
        
        for i in range(60):  # 60 seconds of simulation
            # Compute PID output
            output = pid.compute(current_temp)
            outputs.append(output)
            times.append(i)
            
            # Simple first-order system simulation
            # Temperature change based on damper position
            heat_input = output * 0.5  # Damper effect
            cooling = (current_temp - 25.0) * 0.02  # Ambient cooling
            temp_change = (heat_input - cooling) * 0.1
            
            current_temp += temp_change
            temps.append(current_temp)
            
            if i % 10 == 0:
                state = pid.get_state()
                print(f"t={i:2d}s: Temp={current_temp:6.1f}°C, Output={output:5.1f}%, "
                      f"Error={state.error:6.1f}, P={pid.gains.kp * state.error:5.1f}, "
                      f"I={state.integral:5.1f}, D={state.derivative:5.1f}")
        
        # Check final performance
        final_error = abs(current_temp - target_temp)
        print(f"\nFinal temperature: {current_temp:.1f}°C (target: {target_temp}°C)")
        print(f"Final error: {final_error:.1f}°C")
        print(f"Performance: {'GOOD' if final_error < 2.0 else 'NEEDS_TUNING'}")
        
        # Plot results if matplotlib available
        try:
            plot_pid_results(times, temps[:-1], outputs, target_temp)
        except ImportError:
            print("Matplotlib not available - skipping plot")
        
        return True
        
    except Exception as e:
        logger.error(f"PID controller test failed: {e}")
        return False

def test_temperature_monitor():
    """Test temperature monitoring system"""
    print("\n=== Testing Temperature Monitor ===")
    
    try:
        monitor = TemperatureMonitor(update_interval=0.5, simulate=True)
        
        # Add alert callback
        alerts = []
        def alert_handler(level, message):
            alerts.append((level, message))
            print(f"ALERT [{level}]: {message}")
        
        monitor.add_alert_callback(alert_handler)
        
        print("Starting temperature monitoring...")
        monitor.start_monitoring()
        
        # Monitor for 10 seconds
        for i in range(20):
            time.sleep(0.5)
            
            temps = monitor.get_current_temperatures()
            pit_temp = temps.get("pit_probe")
            
            if pit_temp:
                print(f"Cycle {i+1}: Pit={pit_temp:.1f}°C")
            
            if i == 10:
                # Test probe calibration
                try:
                    monitor.calibrate_probe("pit_probe", 100.0)  # Assume boiling water test
                    print("Probe calibration successful")
                except Exception as e:
                    print(f"Calibration test failed: {e}")
        
        # Check probe status
        probe_status = monitor.get_all_probe_status()
        print(f"\nProbe Status Summary:")
        for probe_name, status in probe_status.items():
            print(f"  {probe_name}: Connected={status.is_connected}, "
                  f"Readings={status.total_readings}, Errors={status.consecutive_errors}")
        
        monitor.stop_monitoring()
        monitor.close()
        
        print(f"Total alerts: {len(alerts)}")
        return True
        
    except Exception as e:
        logger.error(f"Temperature monitor test failed: {e}")
        return False

def test_integrated_controller():
    """Test complete integrated controller"""
    print("\n=== Testing Integrated Controller ===")
    
    try:
        controller = EggBotController(simulate=True)
        
        print("Starting integrated controller...")
        controller.start()
        
        # Test basic operations
        print(f"Initial status: {controller.get_status()}")
        
        # Set setpoint and switch to automatic mode
        controller.set_setpoint(135.0)  # 275°F
        time.sleep(1)
        
        controller.set_control_mode("automatic")
        print("Switched to automatic mode")
        
        # Monitor for 30 seconds
        telemetry_points = []
        
        for i in range(30):
            status = controller.get_status()
            telemetry_points.append({
                'time': i,
                'pit_temp': status.get('pit_temp_c', 0),
                'setpoint': status.get('setpoint_c', 0),
                'damper': status.get('damper_percent', 0),
                'pid_output': status.get('pid_output', 0)
            })
            
            if i % 5 == 0:
                print(f"t={i:2d}s: Pit={status.get('pit_temp_c', 0):.1f}°C, "
                      f"Damper={status.get('damper_percent', 0):.1f}%, "
                      f"Mode={status.get('control_mode', 'unknown')}")
            
            time.sleep(1)
        
        # Test PID preset loading
        print("\nTesting PID presets...")
        presets = controller.get_available_presets()
        print(f"Available presets: {presets}")
        
        for preset in presets[:2]:  # Test first 2 presets
            controller.load_pid_preset(preset)
            gains = controller.get_pid_gains()
            print(f"Loaded {preset}: Kp={gains[0]}, Ki={gains[1]}, Kd={gains[2]}")
            time.sleep(1)
        
        # Test manual mode
        print("\nSwitching to manual mode...")
        controller.set_control_mode("manual")
        controller.set_damper_percent(75.0)
        
        time.sleep(2)
        status = controller.get_status()
        print(f"Manual mode: Damper={status.get('damper_percent', 0):.1f}%")
        
        # Get performance stats
        stats = controller.get_performance_stats()
        print(f"\nPerformance Stats:")
        print(f"  Control loops: {stats['control_loop_count']}")
        print(f"  Telemetry points: {stats['telemetry_points']}")
        print(f"  Connected probes: {stats['connected_probes']}")
        
        # Get probe status
        probe_status = controller.get_probe_status()
        print(f"\nProbe Status:")
        for probe_name, status in probe_status.items():
            print(f"  {probe_name}: Connected={status['connected']}")
        
        controller.stop()
        
        # Plot integrated results if possible
        try:
            plot_integrated_results(telemetry_points)
        except ImportError:
            print("Matplotlib not available - skipping plot")
        
        return True
        
    except Exception as e:
        logger.error(f"Integrated controller test failed: {e}")
        return False

def plot_pid_results(times: List[int], temps: List[float], outputs: List[float], setpoint: float):
    """Plot PID controller results"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    
    # Temperature plot
    ax1.plot(times, temps, 'b-', label='Temperature', linewidth=2)
    ax1.axhline(y=setpoint, color='r', linestyle='--', label='Setpoint')
    ax1.set_ylabel('Temperature (°C)')
    ax1.set_title('PID Controller Response')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Output plot
    ax2.plot(times, outputs, 'g-', label='PID Output', linewidth=2)
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Output (%)')
    ax2.set_ylim(0, 100)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('pid_test_results.png', dpi=150, bbox_inches='tight')
    print("PID results saved to pid_test_results.png")
    plt.close()

def plot_integrated_results(telemetry: List[Dict]):
    """Plot integrated controller results"""
    times = [point['time'] for point in telemetry]
    pit_temps = [point['pit_temp'] for point in telemetry]
    setpoints = [point['setpoint'] for point in telemetry]
    damper_positions = [point['damper'] for point in telemetry]
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    
    # Temperature plot
    ax1.plot(times, pit_temps, 'b-', label='Pit Temperature', linewidth=2)
    ax1.plot(times, setpoints, 'r--', label='Setpoint', linewidth=2)
    ax1.set_ylabel('Temperature (°C)')
    ax1.set_title('Integrated Controller Performance')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Damper plot
    ax2.plot(times, damper_positions, 'g-', label='Damper Position', linewidth=2)
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Damper (%)')
    ax2.set_ylim(0, 100)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('integrated_test_results.png', dpi=150, bbox_inches='tight')
    print("Integrated results saved to integrated_test_results.png")
    plt.close()

def main():
    """Run all PID system tests"""
    print("Pi-Native EggBot PID System Test")
    print("=" * 45)
    
    tests = [
        ("PID Controller", test_pid_controller),
        ("Temperature Monitor", test_temperature_monitor),
        ("Integrated Controller", test_integrated_controller)
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
        print("All tests passed! PID system ready for production.")
        return 0
    else:
        print("Some tests failed. Check logs and configuration.")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nTest suite interrupted")
        sys.exit(130)