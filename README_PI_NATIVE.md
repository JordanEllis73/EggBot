# EggBot Pi-Native Implementation

Complete rewrite of EggBot to run natively on Raspberry Pi 4, eliminating the Arduino dependency and providing enhanced control capabilities.

## 🚀 Key Features

### Hardware Improvements
- **Direct Pi GPIO control** - No Arduino/microcontroller needed
- **16-bit ADC precision** - ADS1115 vs 10-bit Arduino ADC
- **Up to 4 temperature probes** - Pit, meat (2x), and ambient monitoring
- **Hardware PWM servo control** - More precise damper positioning
- **I2C communication** - Reliable, high-speed sensor interface

### Software Enhancements
- **Advanced PID controller** - Anti-windup, derivative filtering, multiple presets
- **Safety systems** - Temperature limits, rate monitoring, emergency shutdown
- **Real-time telemetry** - Enhanced data logging and monitoring
- **Probe calibration** - Individual probe offset adjustment
- **Performance monitoring** - System diagnostics and statistics

## 📋 Hardware Requirements

### Required Components
- **Raspberry Pi 4** (4GB+ recommended)
- **ADS1115 16-bit ADC** - I2C interface
- **Standard servo motor** - For damper control (e.g., SG90, MG996R)
- **NTC thermistors** - 10kΩ recommended (up to 4 probes)
- **10kΩ resistors** - For voltage divider circuits (one per probe)

### Wiring Diagram
```
Raspberry Pi 4 Connections:
┌─────────────────────┐
│ GPIO 2  (SDA) ──────┼── ADS1115 SDA
│ GPIO 3  (SCL) ──────┼── ADS1115 SCL  
│ GPIO 18 (PWM) ──────┼── Servo Signal
│ 3.3V ───────────────┼── ADS1115 VCC
│ GND ────────────────┼── ADS1115 GND, Servo GND
│ 5V ─────────────────┼── Servo VCC
└─────────────────────┘

ADS1115 ADC Channels:
┌─────────────────────┐
│ A0 ─────────────────┼── Pit Thermistor (Voltage Divider)
│ A1 ─────────────────┼── Meat Probe 1 (Voltage Divider)
│ A2 ─────────────────┼── Meat Probe 2 (Voltage Divider)
│ A3 ─────────────────┼── Ambient Probe (Voltage Divider)
└─────────────────────┘

Thermistor Voltage Divider (per probe):
3.3V ── 10kΩ ── ADC_IN ── Thermistor ── GND
```

## 🛠️ Installation

### Quick Setup (Recommended)
```bash
# Clone repository
git clone <repository-url>
cd EggBot

# Switch to Pi-native branch
git checkout pi-native-rewrite

# Run automated setup
./setup_pi_environment.sh

# Reboot to enable I2C
sudo reboot

# Test hardware after reboot
./test_hardware_setup.py
```

### Manual Setup
```bash
# Enable I2C interface
sudo raspi-config
# Navigate to: Interface Options -> I2C -> Enable

# Install system dependencies  
sudo apt update && sudo apt install -y \
    python3-dev python3-pip python3-venv \
    i2c-tools python3-smbus pigpio python3-pigpio

# Enable pigpio daemon
sudo systemctl enable pigpiod
sudo systemctl start pigpiod

# Create Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r pi_native/requirements-pi.txt

# Test installation
python test_hardware_integration.py
```

## 🎛️ Configuration

### Hardware Configuration
Edit `pi_native/config/hardware.py`:
```python
# GPIO pin assignments
GPIO_SERVO_PIN = 18        # PWM-capable pin
I2C_SDA_PIN = 2           # I2C data
I2C_SCL_PIN = 3           # I2C clock

# ADC configuration
ADC_I2C_ADDRESS = 0x48    # ADS1115 address
ADC_SUPPLY_VOLTAGE = 3.3  # Reference voltage
```

### PID Configuration  
Available presets in `pi_native/config/pid.py`:
- **conservative** - Stable, slower response
- **aggressive** - Fast response, higher overshoot risk
- **precise** - Balanced performance  
- **slow_cook** - Gentle control for low temperatures
- **high_temp** - Fast response for high-temperature cooking

### Environment Variables
Create `.env` file:
```bash
PI_NATIVE=true
SIMULATE=false
LOG_LEVEL=INFO
GPIO_SERVO_PIN=18
I2C_ADDRESS=0x48
```

## 🚀 Running

### Development Mode
```bash
# Activate virtual environment
source venv/bin/activate

# Start API server
python -m uvicorn api.app.main:app --host 0.0.0.0 --port 8000 --reload

# Start UI (separate terminal)
cd ui
npm install
npm run dev
```

### Production Mode
```bash
# Enable and start systemd service
sudo systemctl enable eggbot
sudo systemctl start eggbot

# Check status
sudo systemctl status eggbot

# View logs
journalctl -u eggbot -f
```

### Docker Deployment
```bash
# Build and run Pi-native containers
docker-compose -f docker-compose.pi-native.yml up -d

# View logs
docker-compose -f docker-compose.pi-native.yml logs -f
```

## 🔧 Testing

### Hardware Tests
```bash
# Basic hardware connectivity
./test_hardware_setup.py

# Comprehensive integration test
python test_hardware_integration.py

# PID system validation
python test_pid_system.py
```

### API Tests
```bash
# Test enhanced API endpoints
curl http://localhost:8000/pi/system/status
curl http://localhost:8000/pi/temperatures
curl http://localhost:8000/pi/probes/status
```

## 📊 API Endpoints

### Legacy Compatibility
All existing endpoints remain functional:
- `GET /status` - System status
- `POST /setpoint` - Set pit temperature
- `POST /damper` - Manual damper control
- `GET /telemetry` - Historical data

### Enhanced Pi-Native Endpoints
- `GET /pi/system/status` - Comprehensive system status
- `GET /pi/temperatures` - All probe temperatures
- `GET /pi/probes/status` - Detailed probe information
- `GET /pi/telemetry/enhanced` - Multi-probe telemetry
- `GET /pi/pid/tuning-info` - PID tuning diagnostics
- `POST /pi/pid/preset/load` - Load PID presets
- `POST /pi/probes/calibrate` - Calibrate temperature probes
- `GET /pi/system/performance` - Performance statistics
- `POST /pi/safety/reset` - Reset safety shutdown

## 🛡️ Safety Features

### Temperature Safety
- **Maximum temperature limits** - Configurable per probe type
- **Rate limiting** - Detects rapid temperature changes
- **Emergency shutdown** - Automatic damper closure on critical alerts
- **Probe monitoring** - Disconnect detection and warnings

### System Safety  
- **Watchdog monitoring** - Automatic restart on failures
- **Graceful degradation** - Fallback to manual mode on errors
- **Comprehensive logging** - Detailed audit trail
- **Configuration backups** - Automatic backup creation

## 📈 Monitoring

### Web Interface
- **Multi-probe dashboard** - Real-time temperature display
- **Enhanced charts** - All probes on single graph
- **System diagnostics** - Performance and health monitoring
- **Safety status** - Alert and warning display

### Logging
- **Application logs** - `/home/pi/.eggbot/logs/eggbot.log`
- **System logs** - `journalctl -u eggbot`
- **Performance metrics** - Available via API

## 🔄 Migration from Arduino Version

### Automatic Migration
The Pi-native version maintains full API compatibility:
1. Existing frontend works without changes
2. All configuration settings preserved
3. Telemetry data format compatible
4. Gradual feature adoption possible

### Benefits After Migration
- **Higher precision** - 16-bit vs 10-bit temperature readings
- **Lower latency** - Direct hardware control vs serial
- **More probes** - 4 channels vs 1-2 with Arduino  
- **Better reliability** - No USB/serial connection issues
- **Enhanced features** - Advanced PID, safety systems, diagnostics

## 🐛 Troubleshooting

### I2C Issues
```bash
# Check I2C is enabled
sudo raspi-config

# Scan for devices
i2cdetect -y 1

# Check permissions
sudo usermod -a -G i2c $USER
```

### GPIO Issues
```bash
# Check pigpio daemon
sudo systemctl status pigpiod

# Test GPIO access
pigs --version
```

### Temperature Reading Issues
```bash
# Test thermistor calculations
python -c "
from pi_native.hardware.thermistor_calc import ThermistorCalculator
calc = ThermistorCalculator()
temp = calc.voltage_to_temperature(1.5, 0)
print(f'Temperature: {temp}°C')
"
```

### Service Issues
```bash
# Check service status
sudo systemctl status eggbot

# Restart service
sudo systemctl restart eggbot

# View detailed logs
journalctl -u eggbot -f --no-pager
```

## 📚 Development

### Architecture Overview
```
pi_native/
├── hardware/          # Hardware abstraction layer
│   ├── ads1115_manager.py      # I2C ADC interface
│   ├── servo_controller.py     # PWM servo control  
│   └── thermistor_calc.py      # Temperature calculations
├── control/           # Control algorithms
│   ├── pid_controller.py       # Advanced PID implementation
│   ├── temperature_monitor.py  # Multi-probe monitoring
│   └── eggbot_controller.py    # Main controller orchestration
└── config/            # Configuration management
    ├── hardware.py             # Hardware settings
    └── pid.py                  # PID tuning presets
```

### Adding New Features
1. **Hardware components** - Extend hardware abstraction layer
2. **Control algorithms** - Add new control modules
3. **API endpoints** - Create new FastAPI routes  
4. **Frontend features** - Enhance React components

### Testing Framework
- **Unit tests** - Individual component testing
- **Integration tests** - Hardware interaction testing
- **System tests** - End-to-end functionality testing
- **Performance tests** - Control loop timing validation

## 📄 License

Same license as original EggBot project.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Test thoroughly on actual hardware
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open Pull Request

## 📞 Support

- **Issues** - GitHub Issues for bug reports
- **Discussions** - GitHub Discussions for questions
- **Documentation** - This README and inline code comments