import threading
import os
import time
from typing import Optional
from app.config import settings

# Always use Pi-native controller (Arduino support removed)
try:
    from app.pi_native_io import PiNativeControllerIO as ControllerIO
    print("Using Pi-native controller")
except ImportError as e:
    print(f"ERROR: Pi-native controller unavailable: {e}")
    raise RuntimeError("Pi-native controller required but not available")

# Global singleton instance with explicit locking
_controller_instance: Optional[ControllerIO] = None
_controller_lock = threading.Lock()
_instance_count = 0
_process_id = os.getpid()

def get_controller() -> ControllerIO:
    global _controller_instance, _instance_count
    
    with _controller_lock:
        if _controller_instance is None:
            _instance_count += 1
            print(f"CREATING CONTROLLER INSTANCE #{_instance_count} in PID {_process_id}")
            _controller_instance = ControllerIO()
            print(f"Controller instance created: {id(_controller_instance)} in process {_process_id}")
        else:
            print(f"REUSING existing controller instance: {id(_controller_instance)} in process {_process_id}")
        
        return _controller_instance

