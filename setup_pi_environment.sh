#!/bin/bash
# Pi-native EggBot environment setup script for Raspberry Pi 4

set -e

echo "Setting up Pi-native EggBot environment..."

# Update system packages
echo "Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install system dependencies
echo "Installing system dependencies..."
sudo apt install -y \
    python3-dev \
    python3-pip \
    python3-venv \
    git \
    i2c-tools \
    python3-smbus \
    libgpiod2 \
    pigpio \
    python3-pigpio \
    build-essential \
    cmake \
    pkg-config \
    libfreetype6-dev \
    libpng-dev \
    libjpeg-dev \
    libopenblas-dev

# Enable I2C interface
echo "Enabling I2C interface..."
if ! grep -q "^dtparam=i2c_arm=on" /boot/config.txt; then
    echo "dtparam=i2c_arm=on" | sudo tee -a /boot/config.txt
fi

# Enable SPI (sometimes needed for displays)
if ! grep -q "^dtparam=spi=on" /boot/config.txt; then
    echo "dtparam=spi=on" | sudo tee -a /boot/config.txt  
fi

# Add user to gpio group
echo "Adding user to gpio group..."
sudo usermod -a -G gpio $USER

# Enable and start pigpio daemon
echo "Setting up pigpio daemon..."
sudo systemctl enable pigpiod
sudo systemctl start pigpiod

# Create Python virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r pi_native/requirements-pi.txt

# Install Adafruit CircuitPython libraries
echo "Installing Adafruit CircuitPython libraries..."
pip install adafruit-circuitpython-ads1x15
pip install adafruit-blinka

# Create systemd service for EggBot
echo "Creating systemd service..."
sudo tee /etc/systemd/system/eggbot.service > /dev/null <<EOF
[Unit]
Description=EggBot Pi-Native Controller
After=network.target pigpiod.service
Requires=pigpiod.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
Environment=PYTHONPATH=$(pwd)
ExecStart=$(pwd)/venv/bin/python -m uvicorn api.app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create configuration directory
echo "Creating configuration directories..."
mkdir -p /home/$USER/.eggbot
mkdir -p /home/$USER/.eggbot/logs
mkdir -p /home/$USER/.eggbot/backups

# Create environment configuration
echo "Creating environment configuration..."
tee .env > /dev/null <<EOF
# Pi-Native EggBot Configuration
PI_NATIVE=true
SIMULATE=false
LOG_LEVEL=INFO
LOG_FILE=/home/$USER/.eggbot/logs/eggbot.log

# Hardware Configuration
GPIO_SERVO_PIN=18
I2C_ADDRESS=0x48
ADC_SUPPLY_VOLTAGE=3.3

# Control Configuration  
PID_SAMPLE_TIME=1.0
TELEMETRY_INTERVAL=5.0
MAIN_LOOP_INTERVAL=0.25

# Safety Configuration
MAX_PIT_TEMP=400.0
HIGH_TEMP_WARNING=350.0
TEMP_RATE_LIMIT=10.0
PROBE_TIMEOUT=30.0
EOF

# Create backup script
echo "Creating backup script..."
tee backup_config.sh > /dev/null <<'EOF'
#!/bin/bash
# Backup EggBot configuration and logs

BACKUP_DIR="/home/$USER/.eggbot/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/eggbot_backup_$TIMESTAMP.tar.gz"

echo "Creating backup: $BACKUP_FILE"

tar -czf "$BACKUP_FILE" \
    .env \
    pi_native/config/ \
    /home/$USER/.eggbot/logs/ \
    --exclude='*.pyc' \
    --exclude='__pycache__'

echo "Backup created: $BACKUP_FILE"

# Keep only last 10 backups
cd "$BACKUP_DIR"
ls -t eggbot_backup_*.tar.gz | tail -n +11 | xargs -r rm

echo "Old backups cleaned up"
EOF

chmod +x backup_config.sh

# Test I2C connection
echo "Testing I2C connection..."
if command -v i2cdetect >/dev/null 2>&1; then
    echo "I2C devices detected:"
    i2cdetect -y 1 || echo "No I2C devices found or permission denied"
else
    echo "i2c-tools not available for testing"
fi

# Test pigpio
echo "Testing pigpio daemon..."
if pigs --version >/dev/null 2>&1; then
    echo "pigpio daemon is running"
else
    echo "Warning: pigpio daemon not responding"
fi

# Create test script
echo "Creating hardware test script..."
tee test_hardware_setup.py > /dev/null <<'EOF'
#!/usr/bin/env python3
"""Quick hardware test for Pi-native setup"""

import sys
import time

def test_imports():
    """Test that all required modules can be imported"""
    try:
        import board
        import busio  
        import adafruit_ads1x15.ads1115 as ADS
        import pigpio
        print("✓ All required modules imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_i2c():
    """Test I2C bus access"""
    try:
        import board
        import busio
        i2c = busio.I2C(board.SCL, board.SDA)
        print("✓ I2C bus accessible")
        return True
    except Exception as e:
        print(f"✗ I2C test failed: {e}")
        return False

def test_pigpio():
    """Test pigpio daemon connection"""
    try:
        import pigpio
        pi = pigpio.pi()
        if pi.connected:
            pi.stop()
            print("✓ pigpio daemon connection successful")
            return True
        else:
            print("✗ pigpio daemon not connected")
            return False
    except Exception as e:
        print(f"✗ pigpio test failed: {e}")
        return False

def main():
    print("Pi-Native EggBot Hardware Test")
    print("=" * 40)
    
    tests = [
        ("Module Imports", test_imports),
        ("I2C Bus Access", test_i2c), 
        ("pigpio Daemon", test_pigpio)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\nTesting {test_name}...")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 40)
    print("TEST SUMMARY")
    print("=" * 40)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Hardware setup looks good.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
EOF

chmod +x test_hardware_setup.py

echo ""
echo "🎉 Pi-native EggBot setup complete!"
echo ""
echo "Next steps:"
echo "1. Reboot to enable I2C: sudo reboot"
echo "2. Test hardware: ./test_hardware_setup.py"
echo "3. Run hardware integration test: python test_hardware_integration.py"
echo "4. Start EggBot service: sudo systemctl enable eggbot && sudo systemctl start eggbot"
echo "5. Check service status: sudo systemctl status eggbot"
echo ""
echo "Configuration files:"
echo "- Environment: .env"
echo "- Service: /etc/systemd/system/eggbot.service"
echo "- Logs: /home/$USER/.eggbot/logs/"
echo "- Backups: ./backup_config.sh"
echo ""
echo "Web interface will be available at: http://$(hostname -I | awk '{print $1}'):8000"