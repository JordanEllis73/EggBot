#!/usr/bin/env python3
"""
Test script to verify pi_native module imports work correctly
Run this inside the Docker container to test the Python path setup
"""

import sys
import os

print("🧪 Testing pi_native module imports...")
print(f"Python path: {sys.path}")
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
print(f"Working directory: {os.getcwd()}")

# Test 1: Basic pi_native import
try:
    import pi_native
    print("✅ pi_native module import successful")
except ImportError as e:
    print(f"❌ pi_native import failed: {e}")
    sys.exit(1)

# Test 2: Import specific submodules
try:
    from pi_native.control.eggbot_controller import EggBotController
    print("✅ EggBotController import successful")
except ImportError as e:
    print(f"❌ EggBotController import failed: {e}")
    sys.exit(1)

# Test 3: Import config modules
try:
    from pi_native.config.pid import default_control_config, PID_PRESETS
    print("✅ PID config imports successful")
except ImportError as e:
    print(f"❌ PID config imports failed: {e}")
    sys.exit(1)

# Test 4: Import hardware modules
try:
    from pi_native.hardware.ads1115_manager import ADS1115Manager
    print("✅ ADS1115Manager import successful")
except ImportError as e:
    print(f"❌ ADS1115Manager import failed: {e}")
    sys.exit(1)

# Test 5: Test the main API import
try:
    from app.pi_native_io import PiNativeControllerIO
    print("✅ PiNativeControllerIO import successful")
except ImportError as e:
    print(f"❌ PiNativeControllerIO import failed: {e}")
    sys.exit(1)

print("\n🎉 All pi_native imports successful!")
print("✅ Container is ready for pi-native operation")