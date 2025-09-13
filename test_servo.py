#!/usr/bin/env python3

import pigpio
import time
import sys

servo_pin = 18

try:
    pi = pigpio.pi()
    if not pi.connected:
        print("Failed to connect to pigpio daemon")
        sys.exit(1)
    
    print("Connected to pigpio daemon")
    
    def set_angle(angle):
        # Convert angle (0-180) to pulse width (500-2500 microseconds)
        pulse_width = 500 + (angle / 180) * 2000
        pi.set_servo_pulsewidth(servo_pin, pulse_width)
        print(f"Set servo to {angle}° (pulse width: {pulse_width}μs)")
    
    print("Starting servo test - press Ctrl+C to stop")
    
    while True:
        set_angle(0)
        time.sleep(2)
        set_angle(90)
        time.sleep(2)
        set_angle(180)
        time.sleep(2)
        
except KeyboardInterrupt:
    print("\nStopping servo test...")
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'pi' in locals():
        pi.set_servo_pulsewidth(servo_pin, 0)  # Turn off servo
        pi.stop()
        print("Cleaned up pigpio connection")