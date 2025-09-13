#!/usr/bin/env python3
"""
Simplified test to analyze the threading behavior
"""
import threading
import time
from datetime import datetime

class MockControllerIO:
    def __init__(self):
        self._lock = threading.Lock()
        self._setpoint_c = 110.0
        self._meat_setpoint_c = 98.0
        self._running = True
        
        print(f"[CONTROLLER {id(self)}] INIT: setpoint={self._setpoint_c}")
        
        # Start background thread
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
    
    def set_setpoint(self, c: float) -> None:
        with self._lock:
            print(f"[CONTROLLER {id(self)}] setting setpoint to {c} C (was {self._setpoint_c})")
            self._setpoint_c = c
    
    def get_setpoint(self) -> float:
        with self._lock:
            return self._setpoint_c
    
    def get_status(self) -> dict:
        with self._lock:
            status_map = {
                "setpoint_c": self._setpoint_c,
                "meat_setpoint_c": self._meat_setpoint_c,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
            print(f"[CONTROLLER {id(self)}] get_status call: {status_map}")
            return status_map
    
    def _loop(self) -> None:
        """Background thread that might interfere"""
        while self._running:
            # Simulate background processing
            with self._lock:
                # Just read values, don't modify
                current = self._setpoint_c
                print(f"[CONTROLLER {id(self)}] background thread sees setpoint: {current}")
            time.sleep(1.0)

def test_race_condition():
    print("=== Testing Race Condition ===")
    
    # Create controller
    controller = MockControllerIO()
    time.sleep(0.5)  # Let background thread start
    
    # Test rapid setpoint changes
    print("\n--- Rapid Setpoint Changes ---")
    
    def set_130():
        for i in range(3):
            controller.set_setpoint(130.0)
            time.sleep(0.1)
    
    def set_110():
        for i in range(3):
            controller.set_setpoint(110.0)
            time.sleep(0.1)
    
    def monitor_status():
        for i in range(6):
            controller.get_status()
            time.sleep(0.1)
    
    # Run threads concurrently
    threads = [
        threading.Thread(target=set_130),
        threading.Thread(target=set_110), 
        threading.Thread(target=monitor_status)
    ]
    
    for t in threads:
        t.start()
    
    for t in threads:
        t.join()
    
    # Final status
    print("\n--- Final Status ---")
    final = controller.get_status()
    print(f"Final setpoint: {final['setpoint_c']}")
    
    controller._running = False

if __name__ == "__main__":
    test_race_condition()