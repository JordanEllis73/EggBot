#!/usr/bin/env python3
"""
I2C Container Debug Script for EggBot Docker Deployment
Tests I2C functionality within Docker containers on Raspberry Pi

Run this inside the Docker container to diagnose I2C issues:
docker exec -it <container_name> python debug_i2c_container.py
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def print_separator(title):
    """Print a section separator"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def check_environment():
    """Check container environment and variables"""
    print_separator("CONTAINER ENVIRONMENT")

    # Check environment variables
    env_vars = [
        'PI_NATIVE', 'BLINKA_FORCEBOARD', 'BLINKA_FORCECHIP',
        'BLINKA_FORCEI2C', 'PYTHONPATH', 'LOG_LEVEL'
    ]

    for var in env_vars:
        value = os.environ.get(var, 'NOT SET')
        print(f"{var}: {value}")

    # Check user and groups
    try:
        result = subprocess.run(['id'], capture_output=True, text=True)
        print(f"\nUser info: {result.stdout.strip()}")
    except Exception as e:
        print(f"Error getting user info: {e}")

def check_device_access():
    """Check I2C device access"""
    print_separator("DEVICE ACCESS")

    devices_to_check = ['/dev/i2c-1', '/dev/gpiomem', '/dev/mem']

    for device in devices_to_check:
        if Path(device).exists():
            try:
                stat = Path(device).stat()
                print(f"✓ {device} exists (mode: {oct(stat.st_mode)}, owner: {stat.st_uid}:{stat.st_gid})")
            except Exception as e:
                print(f"⚠ {device} exists but cannot stat: {e}")
        else:
            print(f"✗ {device} not found")

def check_i2c_tools():
    """Check I2C tools availability"""
    print_separator("I2C TOOLS")

    # Check if i2cdetect is available
    try:
        result = subprocess.run(['which', 'i2cdetect'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ i2cdetect available")

            # Try to scan I2C bus
            try:
                result = subprocess.run(['i2cdetect', '-y', '1'],
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print("✓ I2C bus scan successful:")
                    print(result.stdout)

                    # Check for ADS1115 at 0x48
                    if '48' in result.stdout:
                        print("✓ ADS1115 detected at address 0x48")
                    else:
                        print("⚠ ADS1115 not detected at 0x48")
                else:
                    print(f"✗ I2C scan failed: {result.stderr}")
            except subprocess.TimeoutExpired:
                print("✗ I2C scan timed out")
            except Exception as e:
                print(f"✗ I2C scan error: {e}")
        else:
            print("✗ i2cdetect not available")
    except Exception as e:
        print(f"✗ Error checking i2cdetect: {e}")

def check_python_libraries():
    """Check Python I2C library availability"""
    print_separator("PYTHON LIBRARIES")

    # Test our safe imports from ADS1115Manager
    try:
        sys.path.insert(0, '/app/pi_native')
        from pi_native.hardware.ads1115_manager import BLINKA_AVAILABLE, SMBUS_AVAILABLE, HARDWARE_AVAILABLE

        if BLINKA_AVAILABLE:
            print("✓ Adafruit Blinka libraries available")
            try:
                from pi_native.hardware.ads1115_manager import board
                if board:
                    print(f"  Board ID: {getattr(board, 'board_id', 'Unknown')}")
            except Exception as e:
                print(f"  ⚠ Cannot get board ID: {e}")
        else:
            print("✗ Blinka libraries not available")

        if SMBUS_AVAILABLE:
            print("✓ SMBus2 library available")
        else:
            print("✗ SMBus2 library not available")

        print(f"Overall hardware support: {'✓' if HARDWARE_AVAILABLE else '✗'}")

    except ImportError as e:
        print(f"✗ Cannot import ADS1115Manager: {e}")
    except Exception as e:
        print(f"✗ Library check error: {e}")

    # Test platform detection safely
    try:
        import adafruit_platformdetect.detector as detector
        print(f"✓ Platform detection: {detector.board.id}")
    except ImportError as e:
        print(f"✗ Platform detection not available: {e}")
    except Exception as e:
        print(f"⚠ Platform detection error: {e}")

def test_i2c_access():
    """Test actual I2C communication"""
    print_separator("I2C COMMUNICATION TEST")

    # Test with SMBus2 first (more reliable in containers)
    try:
        import smbus2
        print("Testing SMBus2 I2C communication...")

        bus = smbus2.SMBus(1)

        # Try to read from ADS1115 config register
        try:
            config = bus.read_word_data(0x48, 0x01)
            print(f"✓ SMBus2: Successfully read ADS1115 config: 0x{config:04x}")
            bus.close()
        except Exception as e:
            print(f"✗ SMBus2: Failed to read ADS1115: {e}")
            bus.close()

    except ImportError:
        print("✗ SMBus2 not available for testing")
    except Exception as e:
        print(f"✗ SMBus2 test error: {e}")

    # Test with Blinka using safe imports
    try:
        sys.path.insert(0, '/app/pi_native')
        from pi_native.hardware.ads1115_manager import BLINKA_AVAILABLE, board, busio, ADS

        if BLINKA_AVAILABLE and board and busio and ADS:
            print("\nTesting Blinka I2C communication...")
            i2c = busio.I2C(board.SCL, board.SDA)
            adc = ADS.ADS1115(i2c, address=0x48)
            print("✓ Blinka: Successfully initialized ADS1115")
        else:
            print("\n✗ Blinka libraries not available for testing")

    except Exception as e:
        print(f"\n✗ Blinka: Failed to initialize ADS1115: {e}")

def test_ads1115_manager():
    """Test the actual ADS1115Manager class"""
    print_separator("ADS1115MANAGER TEST")

    try:
        # Add pi_native to path
        sys.path.insert(0, '/app/pi_native')

        from pi_native.hardware.ads1115_manager import ADS1115Manager

        print("Testing ADS1115Manager initialization...")

        # Test with auto-detection
        manager = ADS1115Manager(simulate=False)
        print(f"✓ ADS1115Manager initialized (SMBus: {manager.use_smbus}, Simulate: {manager.simulate})")

        if not manager.simulate:
            # Test reading a channel
            reading = manager.read_channel(0)
            if reading:
                print(f"✓ Channel 0 reading: {reading.voltage:.3f}V (raw: {reading.raw_value})")
            else:
                print("✗ Failed to read channel 0")

        manager.close()

    except ImportError as e:
        print(f"✗ Cannot import ADS1115Manager: {e}")
    except Exception as e:
        print(f"✗ ADS1115Manager test failed: {e}")

def main():
    """Run all diagnostic tests"""
    print_separator("I2C CONTAINER DIAGNOSTIC")
    print("EggBot Docker I2C Debug Script")
    print("Testing I2C functionality within Docker container")

    check_environment()
    check_device_access()
    check_i2c_tools()
    check_python_libraries()
    test_i2c_access()
    test_ads1115_manager()

    print_separator("DIAGNOSTIC COMPLETE")
    print("\nIf you see errors above:")
    print("1. Check docker-compose.yml has correct device mappings")
    print("2. Verify I2C is enabled on the host: sudo raspi-config")
    print("3. Test host I2C: sudo i2cdetect -y 1")
    print("4. Check container permissions and group membership")

if __name__ == "__main__":
    main()