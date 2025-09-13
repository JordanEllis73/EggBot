# Arduino Integration Notes for serial_io.py

## Current Compatibility

The existing `serial_io.py` is already compatible with the Arduino firmware! No major changes needed because:

1. **JSON Protocol**: Both use JSON messages over serial
2. **Baud Rate**: Both use 115200 (configurable via settings)
3. **Message Format**: Arduino sends exactly what Python expects:
   ```json
   {"pit_temp_c": 125.5, "meat_temp_c": 65.2}
   ```

## Optional Enhancements

If you want to enhance the Python side for better Arduino integration:

### 1. Handle Arduino Acknowledgments
Add this to `_read_line()` method in serial_io.py:
```python
def _read_line(self) -> Optional[dict]:
    if self._simulate:
        return None
    if self._ser and self._ser.readable():
        try:
            line = self._ser.readline().decode("utf-8").strip()
            if not line:
                return None
            try:
                msg = json.loads(line)
                # Handle Arduino acknowledgments and errors
                if "ack" in msg:
                    print(f"Arduino ACK: {msg['ack']} = {msg.get('value', 'N/A')}")
                    return None  # Don't process as temperature data
                elif "error" in msg:
                    print(f"Arduino ERROR: {msg['error']}")
                    return None
                elif "status" in msg:
                    print(f"Arduino STATUS: {msg['status']}")
                    return None
                return msg
            except Exception:
                return None
        except Exception:
            print("Error reading serial")
            return None
    return None
```

### 2. Add Arduino Detection
Add this method to detect Arduino on startup:
```python
def _detect_arduino(self) -> bool:
    """Send a test command to detect if Arduino is responding"""
    if not self._ser:
        return False
    
    try:
        # Send a test command
        test_msg = {"diagnostics": True}
        payload = json.dumps(test_msg) + "\n"
        self._ser.write(payload.encode("utf-8"))
        
        # Wait for response
        start_time = time.time()
        while time.time() - start_time < 3.0:  # 3 second timeout
            if self._ser.in_waiting:
                response = self._ser.readline().decode("utf-8").strip()
                if response:
                    try:
                        msg = json.loads(response)
                        if "diagnostics" in msg or "status" in msg:
                            print("Arduino detected and responding")
                            return True
                    except:
                        pass
            time.sleep(0.1)
        
        print("Arduino not responding to test command")
        return False
    except Exception as e:
        print(f"Arduino detection failed: {e}")
        return False
```

### 3. Enhanced Error Handling
Add retry logic for failed commands:
```python
def _send_with_retry(self, msg: dict, max_retries: int = 3) -> bool:
    """Send message with retry logic"""
    for attempt in range(max_retries):
        try:
            self._send(msg)
            # Wait for acknowledgment (optional)
            time.sleep(0.1)  # Give Arduino time to process
            return True
        except Exception as e:
            print(f"Send attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(0.5)  # Wait before retry
    return False
```

## Testing Arduino Integration

### 1. Hardware Setup
1. Wire Arduino according to README.md schematic
2. Upload eggbot_controller.ino to Arduino
3. Connect Arduino to Raspberry Pi via USB

### 2. Test Serial Communication
```bash
# Test direct serial communication
python3 -c "
import serial
import json
ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
print('Sending test command...')
ser.write(json.dumps({'diagnostics': True}).encode() + b'\n')
response = ser.readline().decode().strip()
print(f'Arduino response: {response}')
ser.close()
"
```

### 3. Test with EggBot API
1. Set environment variable: `export SIMULATE=false`
2. Start the API: `docker-compose up api`
3. Check logs for Arduino communication
4. Test via web UI - servo should move, temperatures should be real

## Troubleshooting

### Common Issues
1. **Permission Denied**: Add user to dialout group
   ```bash
   sudo usermod -a -G dialout $USER
   # Logout and login again
   ```

2. **Wrong Serial Port**: Check available ports
   ```bash
   ls /dev/ttyACM*
   ls /dev/ttyUSB*
   ```

3. **Baud Rate Mismatch**: Ensure both Python and Arduino use 115200

4. **JSON Parsing Errors**: Use Serial Monitor to verify Arduino JSON output

### Verification Commands
```bash
# Check if Arduino is connected
lsusb | grep Arduino

# Monitor serial output
cat /dev/ttyACM0

# Test servo movement manually
echo '{"damper_percent": 50}' > /dev/ttyACM0
```

## Production Deployment

For Raspberry Pi deployment:
1. Update docker-compose.yml to map Arduino device:
   ```yaml
   devices:
     - "/dev/ttyACM0:/dev/ttyACM0"
   ```

2. Ensure container has proper permissions:
   ```yaml
   group_add:
     - "dialout"
   ```

3. Set environment variable:
   ```yaml
   environment:
     - SIMULATE=false
   ```

The existing deployment already includes these settings, so Arduino integration should work out of the box!