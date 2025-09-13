# Pi-Native EggBot Architecture Plan

## Overview
Complete rewrite to eliminate Arduino/microcontroller dependency and run everything natively on Raspberry Pi 4 using:
- **Hardware PWM via pigpio** for servo control
- **I2C with ADS1115** for up to 4 thermistor temperature probes
- **Native Python PID controller** 
- **FastAPI backend** (retained from current architecture)

## Hardware Configuration

### Temperature Sensing
- **ADS1115 16-bit ADC** connected via I2C
- **Up to 4 thermistor probes** (10kΩ NTC recommended)
- **Voltage divider circuits** for each thermistor
- **I2C address**: 0x48 (default for ADS1115)

### Servo Control
- **Single servo** for damper control
- **GPIO Pin 18** (hardware PWM capable)
- **pigpio library** for precise PWM control
- **PWM frequency**: 50Hz (standard servo)

### Wiring Diagram
```
ADS1115:
- VDD → 3.3V
- GND → GND  
- SCL → GPIO 3 (SCL)
- SDA → GPIO 2 (SDA)
- A0-A3 → Thermistor voltage dividers

Servo:
- Signal → GPIO 18
- VCC → 5V
- GND → GND

Thermistor circuits (x4):
3.3V → 10kΩ → ADC_IN → Thermistor → GND
```

## Software Architecture

### Core Components

#### 1. Hardware Layer (`hardware/`)
- `ads1115_manager.py` - I2C communication with ADS1115
- `servo_controller.py` - pigpio servo control
- `thermistor_calc.py` - Temperature calculations

#### 2. Control Layer (`control/`)
- `pid_controller.py` - PID algorithm implementation
- `temperature_monitor.py` - Multi-probe temperature management
- `damper_control.py` - Servo position control

#### 3. API Layer (`api/`)
- Retain existing FastAPI structure
- Update `ControllerIO` for Pi-native hardware
- Extend schemas for multiple temperature probes

#### 4. Configuration (`config/`)
- Hardware pin definitions
- Thermistor calibration parameters
- PID tuning presets

## Key Reusable Components from Current System

### ✅ Keep As-Is
- FastAPI router structure (`routers/controller.py`)
- Basic Pydantic schemas (`models/schemas.py`)
- Health and status endpoints
- Telemetry data structure
- Frontend API integration

### 🔄 Modify/Extend
- `ControllerIO` class - replace serial with direct hardware control
- Temperature data models - extend for multiple probes
- Status schema - add probe identification
- Control modes - enhance for multi-zone control

### ❌ Remove/Replace
- Serial communication (`serial_io.py`)
- Arduino-specific message protocols
- USB/serial port configuration

## Implementation Phases

### Phase 1: Core Hardware Integration
1. ADS1115 I2C communication
2. Thermistor temperature calculations
3. pigpio servo control
4. Hardware abstraction layer

### Phase 2: Control Logic
1. Multi-probe temperature monitoring
2. Enhanced PID controller
3. Damper position control
4. Safety limits and failsafes

### Phase 3: API Integration
1. Update ControllerIO for Pi hardware
2. Extend schemas for multi-probe support
3. Maintain API compatibility where possible
4. Add new endpoints for probe management

### Phase 4: Testing & Validation
1. Hardware integration testing
2. Temperature accuracy validation
3. PID tuning and performance testing
4. System reliability testing

## Dependencies

### New Python Packages
```bash
pip install adafruit-circuitpython-ads1x15
pip install pigpio
pip install board
pip install busio
```

### System Requirements
```bash
sudo apt install pigpio
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

## Configuration Files

### `config/hardware.py`
- GPIO pin assignments
- I2C addresses
- ADC configuration
- Servo parameters

### `config/thermistors.py`
- Steinhart-Hart coefficients
- Voltage divider values
- Calibration offsets
- Probe identification

### `config/pid.py`
- Default PID gains
- Tuning presets
- Control loop timing
- Safety limits

## Migration Strategy

1. **Branch Creation** ✅ - `pi-native-rewrite`
2. **Parallel Development** - Keep existing system functional
3. **Incremental Testing** - Test each component individually
4. **Integration Testing** - Full system validation
5. **Performance Comparison** - Validate against Arduino version
6. **Production Deployment** - Switch to Pi-native when stable

## Benefits of Pi-Native Approach

### Performance
- Direct hardware control (no serial latency)
- Higher resolution temperature readings (16-bit vs 10-bit)
- More precise PWM control
- Faster control loop execution

### Flexibility
- Multiple temperature probes (up to 4)
- Software-configurable parameters
- Real-time calibration adjustments
- Enhanced debugging capabilities

### Reliability
- Fewer hardware components
- No USB/serial connection issues
- Integrated error handling
- Comprehensive logging

### Cost
- Eliminate Arduino hardware cost
- Simpler wiring and assembly
- Reduced power consumption
- Single-board solution

This architecture maintains API compatibility while providing enhanced capabilities and improved performance through native Pi integration.