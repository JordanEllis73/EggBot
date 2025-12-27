# Setting up pigpio to run automatically on Raspberry Pi 4

## Installation
```bash
sudo apt update
sudo apt install pigpio python3-pigpio
pip3 install pigpio
```

## Enable pigpio daemon to start automatically
```bash
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

## Check if pigpio daemon is running
```bash
sudo systemctl status pigpiod
```

## Manual start/stop commands
```bash
# Start daemon manually
sudo pigpiod

# Stop daemon manually
sudo killall pigpiod
```

## Run the servo test
```bash
python3 test_servo.py
```

## Notes
- pigpio daemon must be running before your Python script can connect
- The daemon runs with root privileges to access GPIO
- More precise timing than RPi.GPIO library
- Supports hardware PWM for smoother servo control