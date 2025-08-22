import json
import threading
import time
from datetime import datetime
from typing import Optional, List
from app.config import settings

try:
    import serial  # type: ignore
    import serial.tools.list_ports
except Exception:  # pragma: no cover
    serial = None  # type: ignore


class ControllerIO:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._ser = None
        self._simulate = settings.simulate or (serial is None)

        self._setpoint_c = 110.0  # default ~225F
        self._meat_setpoint_c = 98
        self._damper_percent = 0
        self._pit_temp_c = 25.0
        self._meat_temp_c: Optional[float] = None
        self._telemetry: List[dict] = []

        if not self._simulate:
            self._open_serial()

        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _open_serial(self) -> None:
        try:
            print(
                f"Connecting to Serial on port {settings.serial_port} with baud rate {settings.baud}"
            )
            self._ser = serial.Serial(settings.serial_port, settings.baud, timeout=1)  # type: ignore
        except serial.SerialException as e:
            raise Exception(f"Failed to connect to Arduino: {e}")
        except FileNotFoundError:
            raise Exception("Arduino not found - check USB connection")

    def set_setpoint(self, c: float) -> None:
        with self._lock:
            print(f"setting setpoint to {c} C")
            self._setpoint_c = c
        self._send({"setpoint_c": c})

    def get_setpoint(self) -> float:
        with self._lock:
            return self._setpoint_c

    def set_meat_setpoint(self, c: float) -> None:
        with self._lock:
            print(f"setting meat setpoint to {c} C")
            self._meat_setpoint_c = c
        self._send({"meat_setpoint_c": c})

    def get_meat_setpoint(self) -> None:
        with self._lock:
            return self._meat_setpoint_c

    def set_damper(self, percent: int) -> None:
        percent = max(0, min(100, int(percent)))
        with self._lock:
            self._damper_percent = percent
        self._send({"damper_percent": percent})

    def set_pid_gains(self, kp: float, ki: float, kd: float) -> None:
        with self._lock:
            print(f"Updating PID gains to {kp}, {ki}, {kd}")
            self._pid_gains = [kp, ki, kd]
        self._send({"pid_gains": [kp, ki, kd]})

    def _send(self, msg: dict) -> None:
        if self._simulate:
            return
        if self._ser and self._ser.writable():  # type: ignore
            payload = json.dumps(msg) + "\n"
            print(f"sending payload: {payload}")
            # self._ser.write(payload.encode("utf-8"))  # type: ignore

    def _read_line(self) -> Optional[dict]:
        if self._simulate:
            return None
        if self._ser and self._ser.readable():  # type: ignore
            try:
                line = self._ser.readline().decode("utf-8").strip()  # type: ignore
                if not line:
                    return None
                try:
                    return json.loads(line)
                except Exception:
                    return None
            except Exception:
                print("Error reading serial")
                return None
        return None

    def _simulate_step(self) -> None:
        # Very simple first-order approach: pit temp moves towards setpoint based on damper opening.
        with self._lock:
            sp = self._setpoint_c
            damper = self._damper_percent
            temp = self._pit_temp_c

        ambient = 22.0
        responsiveness = 0.002 + damper * 0.0005
        cooling = 0.0008
        temp += responsiveness * (sp - temp) - cooling * (temp - ambient)

        with self._lock:
            self._pit_temp_c = temp

    def _loop(self) -> None:
        while self._running:
            if self._simulate:
                self._simulate_step()
            else:
                msg = self._read_line()
                if isinstance(msg, dict):
                    with self._lock:
                        self._pit_temp_c = float(
                            msg.get("pit_temp_c", self._pit_temp_c)
                        )
                        meat = msg.get("meat_temp_c")
                        self._meat_temp_c = float(meat) if meat is not None else None

            with self._lock:
                point = {
                    "pit_temp_c": round(self._pit_temp_c, 2),
                    "meat_temp_c": self._meat_temp_c,
                    "damper_percent": self._damper_percent,
                    "setpoint_c": self._setpoint_c,
                    "meat_setpoint_c": self._meat_setpoint_c,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                }
                self._telemetry.append(point)
                if len(self._telemetry) > 1800:  # ~30 min at 1s
                    self._telemetry = self._telemetry[-1800:]

            time.sleep(1.0)

    def get_status(self) -> dict:
        with self._lock:
            status_map = {
                "pit_temp_c": self._pit_temp_c,
                "meat_temp_c": self._meat_temp_c,
                "damper_percent": self._damper_percent,
                "setpoint_c": self._setpoint_c,
                "meat_setpoint_c": self._meat_setpoint_c,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
            print(f"Received get_status call: {status_map}")
            return status_map

    def get_telemetry(self) -> list[dict]:
        with self._lock:
            return list(self._telemetry)
