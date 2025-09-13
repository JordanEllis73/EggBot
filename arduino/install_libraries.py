#!/usr/bin/env python3
"""
Arduino Library Installation Helper for EggBot

This script helps install required Arduino libraries for the EggBot controller.
It provides guidance for manual installation since Arduino library management
is typically done through the Arduino IDE.
"""

import os
import platform
import webbrowser
from pathlib import Path

def print_header(title):
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_step(step_num, title, description):
    print(f"\n{step_num}. {title}")
    print("-" * (len(title) + 3))
    print(description)

def get_arduino_ide_install():
    """Get Arduino IDE installation instructions"""
    system = platform.system().lower()
    
    print_header("Arduino IDE Installation")
    
    if system == "windows":
        print("For Windows:")
        print("1. Download from: https://www.arduino.cc/en/software")
        print("2. Run the installer (.exe file)")
        print("3. Follow the installation wizard")
        
    elif system == "darwin":  # macOS
        print("For macOS:")
        print("1. Download from: https://www.arduino.cc/en/software")
        print("2. Drag Arduino.app to Applications folder")
        print("3. Or install via Homebrew: brew install arduino")
        
    elif system == "linux":
        print("For Linux:")
        print("1. Download from: https://www.arduino.cc/en/software")
        print("2. Extract the tar.gz file")
        print("3. Run: sudo ./install.sh")
        print("4. Or install via package manager:")
        print("   - Ubuntu/Debian: sudo apt install arduino")
        print("   - Fedora: sudo dnf install arduino")
        print("   - Arch: sudo pacman -S arduino")
    
    print("\nOfficial download: https://www.arduino.cc/en/software")

def get_library_instructions():
    """Get library installation instructions"""
    print_header("Required Arduino Libraries")
    
    libraries = [
        {
            "name": "ArduinoJson",
            "author": "Benoit Blanchon",
            "version": "6.21.0 or later",
            "description": "JSON parsing and generation for Arduino",
            "search_term": "ArduinoJson"
        },
        {
            "name": "Servo",
            "author": "Arduino",
            "version": "Built-in",
            "description": "Control servo motors (pre-installed with Arduino IDE)",
            "search_term": "Servo"
        }
    ]
    
    print("The following libraries are required:")
    print()
    
    for i, lib in enumerate(libraries, 1):
        print(f"{i}. {lib['name']} by {lib['author']}")
        print(f"   Version: {lib['version']}")
        print(f"   Description: {lib['description']}")
        print()

def get_installation_steps():
    """Get step-by-step installation guide"""
    print_header("Installation Steps")
    
    print_step(1, "Install Arduino IDE", 
               "Download and install Arduino IDE from arduino.cc")
    
    print_step(2, "Open Library Manager",
               """- Open Arduino IDE
- Go to Sketch → Include Library → Manage Libraries
- Wait for the library index to update""")
    
    print_step(3, "Install ArduinoJson",
               """- In the Library Manager search box, type: ArduinoJson
- Find "ArduinoJson by Benoit Blanchon"
- Click Install (choose version 6.21.0 or later)
- Wait for installation to complete""")
    
    print_step(4, "Verify Servo Library",
               """- Search for "Servo" in Library Manager
- It should show as "INSTALLED" (built-in library)
- If not found, it will be included with Arduino IDE""")
    
    print_step(5, "Test Installation",
               """- Close and reopen Arduino IDE
- Go to Sketch → Include Library
- Verify "ArduinoJson" and "Servo" appear in the list""")

def get_upload_instructions():
    """Get firmware upload instructions"""
    print_header("Firmware Upload Guide")
    
    print_step(1, "Connect Arduino",
               """- Connect Arduino Uno to computer via USB cable
- Ensure Arduino power LED is on""")
    
    print_step(2, "Open Sketch",
               f"""- Open Arduino IDE
- File → Open → Navigate to:
  {os.path.join(os.getcwd(), 'eggbot_controller', 'eggbot_controller.ino')}""")
    
    print_step(3, "Configure Arduino IDE",
               """- Tools → Board → Arduino AVR Boards → Arduino Uno
- Tools → Port → Select your Arduino port:
  - Windows: COM3, COM4, etc.
  - Linux: /dev/ttyACM0, /dev/ttyUSB0
  - macOS: /dev/cu.usbmodem...""")
    
    print_step(4, "Compile and Upload",
               """- Click Verify (✓) button to compile
- Fix any errors if they appear
- Click Upload (→) button to upload to Arduino
- Wait for "Done uploading" message""")
    
    print_step(5, "Test Communication",
               """- Tools → Serial Monitor
- Set baud rate to 115200
- You should see: {"status":"Arduino EggBot Controller Ready","version":"1.0"}""")

def check_arduino_sketch():
    """Check if Arduino sketch exists"""
    sketch_path = Path("eggbot_controller/eggbot_controller.ino")
    
    if sketch_path.exists():
        print(f"✓ Arduino sketch found: {sketch_path.absolute()}")
        return True
    else:
        print(f"✗ Arduino sketch not found: {sketch_path.absolute()}")
        print("  Make sure you're running this script from the arduino/ directory")
        return False

def main():
    print_header("EggBot Arduino Library Installation Helper")
    print("This script provides guidance for installing Arduino libraries")
    print("and uploading the EggBot controller firmware.")
    
    # Check if sketch exists
    sketch_exists = check_arduino_sketch()
    
    # Get system info
    print(f"\nDetected system: {platform.system()} {platform.release()}")
    
    # Provide instructions
    get_arduino_ide_install()
    get_library_instructions()
    get_installation_steps()
    
    if sketch_exists:
        get_upload_instructions()
    
    print_header("Quick Reference")
    print("Required Libraries:")
    print("• ArduinoJson (by Benoit Blanchon) - version 6.21.0+")
    print("• Servo (built-in)")
    print()
    print("Upload Settings:")
    print("• Board: Arduino Uno")
    print("• Port: /dev/ttyACM0 (Linux), COM3+ (Windows), /dev/cu.usbmodem* (macOS)")
    print("• Baud: 115200")
    print()
    print("Test Command:")
    print('echo \'{"diagnostics": true}\' > /dev/ttyACM0')
    print()
    print("For more help, see: arduino/README.md")
    
    # Ask if user wants to open Arduino IDE download page
    try:
        response = input("\nOpen Arduino IDE download page in browser? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            webbrowser.open('https://www.arduino.cc/en/software')
    except KeyboardInterrupt:
        print("\n\nInstallation guide complete!")

if __name__ == "__main__":
    main()