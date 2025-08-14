from functools import lru_cache
from app.serial_io import ControllerIO

# Singleton pattern - creates one instance and reuses it
@lru_cache()
def get_controller() -> ControllerIO:
    return ControllerIO()

