import threading
from typing import Optional
from app.serial_io import ControllerIO

# Global singleton instance with explicit locking
_controller_instance: Optional[ControllerIO] = None
_controller_lock = threading.Lock()
_instance_count = 0

def get_controller() -> ControllerIO:
    global _controller_instance, _instance_count
    
    with _controller_lock:
        if _controller_instance is None:
            _instance_count += 1
            print(f"CREATING CONTROLLER INSTANCE #{_instance_count}")
            _controller_instance = ControllerIO()
            print(f"Controller instance created: {id(_controller_instance)}")
        else:
            print(f"REUSING existing controller instance: {id(_controller_instance)}")
        
        return _controller_instance

