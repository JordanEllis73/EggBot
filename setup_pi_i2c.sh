#!/bin/bash
"""
Raspberry Pi I2C Setup Script for EggBot Docker Deployment
Sets up I2C hardware access for Docker containers

Run this on the Raspberry Pi host before starting Docker containers:
sudo ./setup_pi_i2c.sh
"""

set -e

echo "==============================================="
echo "EggBot Raspberry Pi I2C Setup"
echo "==============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   log_error "This script must be run as root (use sudo)"
   exit 1
fi

# Check if we're on a Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    log_warn "This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 1. Enable I2C interface
log_info "Enabling I2C interface..."
if ! grep -q "^dtparam=i2c_arm=on" /boot/firmware/config.txt; then
    echo "dtparam=i2c_arm=on" >> /boot/firmware/config.txt
    log_info "Added I2C to config.txt"
else
    log_info "I2C already enabled in config.txt"
fi

# Load I2C modules
log_info "Loading I2C kernel modules..."
modprobe i2c-dev || log_warn "Failed to load i2c-dev module"
modprobe i2c-bcm2835 || log_warn "Failed to load i2c-bcm2835 module"

# Add modules to persistent load
if ! grep -q "i2c-dev" /etc/modules; then
    echo "i2c-dev" >> /etc/modules
    log_info "Added i2c-dev to /etc/modules"
fi

if ! grep -q "i2c-bcm2835" /etc/modules; then
    echo "i2c-bcm2835" >> /etc/modules
    log_info "Added i2c-bcm2835 to /etc/modules"
fi

# 2. Install I2C tools
log_info "Installing I2C tools..."
apt-get update
apt-get install -y i2c-tools

# 3. Create I2C and GPIO groups with consistent GIDs
log_info "Setting up hardware access groups..."

# Create i2c group (GID 998 if available)
if ! getent group i2c > /dev/null; then
    groupadd -g 998 i2c || groupadd i2c
    log_info "Created i2c group"
else
    log_info "i2c group already exists"
fi

# Create gpio group (GID 997 if available)
if ! getent group gpio > /dev/null; then
    groupadd -g 997 gpio || groupadd gpio
    log_info "Created gpio group"
else
    log_info "gpio group already exists"
fi

# 4. Set device permissions
log_info "Setting device permissions..."

# Create udev rules for I2C and GPIO access
cat > /etc/udev/rules.d/99-eggbot-i2c.rules << 'EOF'
# EggBot I2C and GPIO device permissions
SUBSYSTEM=="i2c-dev", GROUP="i2c", MODE="0664"
SUBSYSTEM=="gpio", GROUP="gpio", MODE="0664"
KERNEL=="gpiomem", GROUP="gpio", MODE="0664"
KERNEL=="i2c-[0-9]*", GROUP="i2c", MODE="0664"
EOF

log_info "Created udev rules for hardware access"

# Reload udev rules
udevadm control --reload-rules
udevadm trigger

# 5. Set current device permissions (immediate effect)
if [ -e /dev/i2c-1 ]; then
    chown root:i2c /dev/i2c-1
    chmod 664 /dev/i2c-1
    log_info "Set permissions for /dev/i2c-1"
fi

if [ -e /dev/gpiomem ]; then
    chown root:gpio /dev/gpiomem
    chmod 664 /dev/gpiomem
    log_info "Set permissions for /dev/gpiomem"
fi

# 6. Add current user to groups (if not root)
if [ "$SUDO_USER" ]; then
    usermod -a -G i2c,gpio "$SUDO_USER"
    log_info "Added user $SUDO_USER to i2c and gpio groups"
fi

# 7. Test I2C functionality
log_info "Testing I2C functionality..."
if command -v i2cdetect >/dev/null 2>&1; then
    echo "Scanning I2C bus 1:"
    i2cdetect -y 1 || log_warn "I2C scan failed - check hardware connections"

    # Check for ADS1115
    if i2cdetect -y 1 | grep -q " 48 "; then
        log_info "✓ ADS1115 detected at address 0x48"
    else
        log_warn "ADS1115 not detected at 0x48 - check wiring"
    fi
else
    log_error "i2cdetect not available"
fi

# 8. Display group information
echo
log_info "Hardware access groups:"
getent group i2c gpio | while read line; do
    echo "  $line"
done

echo
log_info "Device permissions:"
ls -la /dev/i2c* /dev/gpiomem 2>/dev/null || log_warn "Some devices not found"

echo
echo "==============================================="
log_info "Setup complete!"
echo "==============================================="
echo
echo "Next steps:"
echo "1. Reboot the Pi to ensure all changes take effect:"
echo "   sudo reboot"
echo
echo "2. After reboot, test I2C:"
echo "   sudo i2cdetect -y 1"
echo
echo "3. Start your Docker containers:"
echo "   docker-compose -f docker-compose.pi-native.yml up -d"
echo
echo "4. Test I2C in container:"
echo "   docker exec -it <container_name> python debug_i2c_container.py"
echo

# Check if reboot is recommended
if [ ! -e /dev/i2c-1 ] || [ ! -e /dev/gpiomem ]; then
    log_warn "Hardware devices not fully available - reboot recommended"
fi