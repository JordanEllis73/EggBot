# EggBot Arduino Controller

This folder contains the Arduino firmware for the EggBot temperature controller system. The Arduino acts as a hardware interface, controlling the damper servo and reading thermistor temperatures.

## Hardware Requirements

### Components
- Arduino Uno or compatible microcontroller
- Servo motor (SG90 or similar) for damper control
- 2x 10kΩ NTC thermistors (for pit and meat temperature)
  - NTC = Negative Temperature Coefficient
  - Resistance DECREASES as temperature INCREASES
  - Common types: EPCOS B57164K, Vishay NTCLE100E3, or equivalent
- 2x 10kΩ precision resistors (1% tolerance recommended for voltage dividers)
- Jumper wires and breadboard/PCB

### Wiring Diagram

```
Arduino Uno Pinout:
┌─────────────────────────┐
│  Digital Pin 9  ────────┼──→ Servo Signal (Orange/Yellow)
│  GND            ────────┼──→ Servo Ground (Brown/Black)  
│  5V             ────────┼──→ Servo Power (Red)
│                         │
│  Analog Pin A0  ────────┼──→ Pit Thermistor (via voltage divider)
│  Analog Pin A1  ────────┼──→ Meat Thermistor (via voltage divider)
│  5V             ────────┼──→ Voltage divider VCC
│  GND            ────────┼──→ Voltage divider GND
└─────────────────────────┘

NTC Thermistor Voltage Divider Circuit (for each thermistor):
    5V ──────┬──────── 
             │
           ┌─┴─┐
           │10k│ Reference Resistor (R1)
           │ Ω │ Fixed resistance
           └─┬─┘
             │
             ├──────── To Arduino Analog Pin (A0/A1)
             │         ↑ Voltage measured here
           ┌─┴─┐
           │NTC│ Thermistor (R2) 
           │10k│ Variable resistance (decreases with heat)
           └─┬─┘
             │
           GND ────────

NTC Behavior:
- Room temperature (~25°C): ~10,000Ω → ADC ≈ 512 (mid-range)  
- High temperature (~200°C): ~200Ω → ADC ≈ 950 (high reading)
- Low temperature (~0°C): ~32,000Ω → ADC ≈ 120 (low reading)
```

## Software Requirements

### Arduino Libraries
Install these libraries via Arduino IDE Library Manager:
1. **ArduinoJson** (by Benoit Blanchon) - for JSON communication
2. **Servo** (built-in) - for servo control

### Installation Steps

1. **Install Arduino IDE**: Download from [arduino.cc](https://www.arduino.cc/en/software)

2. **Install Required Libraries**:
   - Open Arduino IDE
   - Go to Sketch → Include Library → Manage Libraries
   - Search for "ArduinoJson" and install the latest version
   - Servo library should be pre-installed

3. **Upload Firmware**:
   - Connect Arduino Uno via USB
   - Open `eggbot_controller.ino` in Arduino IDE
   - Select Board: "Arduino Uno" (Tools → Board)
   - Select correct Port (Tools → Port)
   - Click Upload button

4. **Verify Connection**:
   - Open Serial Monitor (Tools → Serial Monitor)
   - Set baud rate to 115200
   - You should see: `{"status":"Arduino EggBot Controller Ready","version":"1.0"}`

## Configuration

### Pin Configuration
Edit `config.h` to modify pin assignments:
```cpp
#define SERVO_PIN 9                    // PWM pin for damper servo
#define PIT_THERMISTOR_PIN A0         // Analog pin for pit probe
#define MEAT_THERMISTOR_PIN A1        // Analog pin for meat probe
```

### Servo Calibration
Adjust servo angles for your damper mechanism:
```cpp
#define SERVO_MIN_ANGLE 0             // Servo angle for closed damper (0%)
#define SERVO_MAX_ANGLE 90            // Servo angle for open damper (100%)
```

### Thermistor Calibration
The firmware uses Steinhart-Hart coefficients optimized for NTC thermistors. Default coefficients work for common 10kΩ NTC sensors:

```cpp
#define A_COEFF 0.0007343140544   // Optimized for NTC behavior
#define B_COEFF 0.0002157437229   // Accounts for decreasing resistance
#define C_COEFF 0.0000000951568577 // with increasing temperature
```

**Understanding NTC Thermistor Response:**
- **Cold** (0°C): High resistance (~32kΩ) → Low ADC reading (~120)
- **Room** (25°C): Nominal resistance (~10kΩ) → Mid ADC reading (~512)  
- **Hot** (200°C): Low resistance (~200Ω) → High ADC reading (~950)

**To calibrate your specific thermistors:**
1. Measure resistance at known temperatures:
   - Ice water (0°C), Room temperature (~25°C), Boiling water (100°C)
   - Use multimeter to measure actual resistance values
2. Use online Steinhart-Hart calculator (e.g., thinksrs.com calculator)
3. Update coefficients in `config.h`
4. Test with `thermistor_test.ino` to verify accuracy

## Serial Protocol

### Communication Format
- **Baud Rate**: 115200
- **Format**: JSON messages terminated with newline (`\n`)
- **Direction**: Bidirectional

### Incoming Commands (Python → Arduino)
```json
{"setpoint_c": 110.0}           // Set pit temperature target
{"meat_setpoint_c": 65.0}       // Set meat temperature target  
{"damper_percent": 50}           // Set damper position (0-100%)
{"pid_gains": [1.0, 0.1, 0.05]} // Set PID controller gains
```

### Outgoing Status (Arduino → Python)
```json
{
  "pit_temp_c": 125.5,          // Current pit temperature (°C)
  "meat_temp_c": 65.2,          // Current meat temperature (°C)
  "setpoint_c": 110.0,          // Current setpoint confirmation
  "meat_setpoint_c": 65.0,      // Current meat setpoint confirmation
  "damper_percent": 50           // Current damper position confirmation
}
```

### Error Messages
```json
{"error": "Invalid JSON: MissingValue"}
{"error": "Setpoint out of range: 500.0"}
```

### Acknowledgments
```json
{"ack": "setpoint_c", "value": 110.0}
{"ack": "damper_percent", "value": 50}
```

## Troubleshooting

### Common Issues

1. **No Serial Communication**:
   - Check USB connection
   - Verify correct COM port selection
   - Ensure baud rate is 115200 in both Arduino and Python

2. **Invalid Temperature Readings**:
   - Check thermistor wiring and voltage divider circuit
   - Verify 10kΩ reference resistors are correct value (use multimeter)
   - Check for loose connections
   - **NTC-specific issues**:
     - ADC reading stuck at 0 or 1023: Check for short/open circuit
     - Temperature reads extremely high: Thermistor may be shorted
     - Temperature reads extremely low: Thermistor may be open/disconnected
     - Readings unstable: Poor connections or electrical noise

3. **Servo Not Moving**:
   - Verify servo power supply (needs external 5V if using multiple servos)
   - Check servo control wire connection to pin 9
   - Test servo independently with simple sketch

4. **JSON Parse Errors**:
   - Check JSON syntax in commands
   - Ensure messages end with newline character
   - Verify ArduinoJson library is installed

### Diagnostic Commands
Send these via Serial Monitor for debugging:
```json
{"diagnostics": true}           // Get ADC values and system info
```

Response:
```json
{
  "diagnostics": {
    "pit_adc": 512,              // Raw ADC reading (0-1023)
    "meat_adc": 487,             // Raw ADC reading (0-1023)  
    "servo_angle": 45,           // Current servo angle
    "free_ram": 1234             // Available RAM (bytes)
  }
}
```

**Interpreting NTC ADC Values:**
- ADC 0-50: Thermistor likely disconnected (infinite resistance)
- ADC 100-200: Very cold temperature or wrong thermistor type  
- ADC 400-600: Normal room temperature range (~20-30°C)
- ADC 800-950: High cooking temperatures (100-300°C)
- ADC 1000+: Thermistor may be shorted or damaged

## Code Formatting

This project uses Google C++ Style Guide with clang-format for consistent code formatting.

### Automatic Formatting
```bash
# Format all Arduino files
./format_code.sh

# Check formatting without changes  
./format_code.sh --check
```

### Editor Support
- **VSCode**: Configured in `.vscode/settings.json` - formats on save
- **Vim/Neovim**: Uses `.clangd` for LSP support
- **Any Editor**: Uses `.editorconfig` for basic formatting

### Style Guidelines
- **Indentation**: 2 spaces (no tabs)
- **Line Length**: 80 characters max
- **Braces**: Google style (opening brace on same line)
- **Naming**: Variables `camelCase`, functions `camelCase()`, constants `UPPER_CASE`

## Integration with Python API

The Python `serial_io.py` automatically detects and communicates with the Arduino. No changes needed to existing Python code - it will use real hardware instead of simulation when Arduino is connected.

Key integration points:
- Arduino must be connected to `/dev/ttyACM0` (Linux) or `COM3` (Windows)
- Serial baud rate must match `SERIAL_BAUD` setting in Python config
- JSON message format must exactly match protocol specification

## Schematic

```
                    Arduino Uno
                  ┌───────────────┐
                  │               │
                  │ Digital Pin 9 ├─────────┐
                  │               │         │
                  │ Analog Pin A0 ├─────┐   │    Servo Motor
                  │               │     │   │   ┌───────────┐
                  │ Analog Pin A1 ├─┐   │   └───┤ Signal    │
                  │               │ │   │       │           │
                  │           5V  ├─┼───┼───────┤ VCC   SG90│
                  │               │ │   │       │           │
                  │          GND  ├─┼───┼───────┤ GND       │
                  │               │ │   │       └───────────┘
                  └───────────────┘ │   │
                                    │   │
                   Pit Thermistor   │   │   Meat Thermistor
                   ┌─────────────────┘   └─────────────────┐
                   │                                       │
                   │ 5V ──┬─── A0                5V ──┬─── A1
                   │      │                           │
                   │    ┌─┴─┐                       ┌─┴─┐
                   │    │10k│                       │10k│
                   │    │ Ω │                       │ Ω │
                   │    └─┬─┘                       └─┬─┘
                   │      │                           │
                   │      ├── To A0           To A1 ──┤
                   │      │                           │
                   │    ┌─┴─┐                       ┌─┴─┐
                   │    │NTC│                       │NTC│
                   │    │10k│                       │10k│
                   │    └─┬─┘                       └─┬─┘
                   │      │                           │
                   │    GND                        GND
                   └─────────────────────────────────────┘
```

This schematic shows the complete wiring for the EggBot Arduino controller with servo and dual thermistor inputs.