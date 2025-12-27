"""Configuration persistence for EggBot"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Optional
from pi_native.hardware.thermistor_calc import ThermistorConfig, SteinhartHartCoefficients

# Default config directory - uses /app/data for Docker persistence
CONFIG_DIR = Path(os.getenv('EGGBOT_CONFIG_DIR', '/app/data/config'))
CALIBRATION_FILE = CONFIG_DIR / 'probe_calibration.json'


class CalibrationPersistence:
    """Manages persistence of probe calibration offsets"""

    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file or CALIBRATION_FILE
        self._initialized = False

    def _ensure_config_dir(self) -> bool:
        """Ensure config directory exists, return success status"""
        if self._initialized:
            return True

        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            self._initialized = True
            return True
        except PermissionError:
            logging.warning(f"Cannot create config directory {self.config_file.parent}, calibrations will not persist")
            return False
        except Exception as e:
            logging.error(f"Error creating config directory: {e}")
            return False

    def save_calibration(self, probe_name: str, offset_c: float) -> None:
        """Save calibration offset for a probe"""
        if not self._ensure_config_dir():
            logging.warning(f"Cannot save calibration for {probe_name}: config directory not writable")
            return

        try:
            # Load existing calibrations
            calibrations = self._load_all()

            # Update with new calibration
            calibrations[probe_name] = {
                'offset_c': offset_c,
                'calibrated_at': self._get_timestamp()
            }

            # Save to file
            with open(self.config_file, 'w') as f:
                json.dump(calibrations, f, indent=2)

            logging.info(f"Saved calibration for {probe_name}: offset={offset_c:.2f}°C")

        except Exception as e:
            logging.error(f"Failed to save calibration for {probe_name}: {e}")

    def load_calibration(self, probe_name: str) -> Optional[float]:
        """Load calibration offset for a probe"""
        try:
            calibrations = self._load_all()
            if probe_name in calibrations:
                offset = calibrations[probe_name].get('offset_c', 0.0)
                logging.info(f"Loaded calibration for {probe_name}: offset={offset:.2f}°C")
                return offset
            return None
        except Exception as e:
            logging.error(f"Failed to load calibration for {probe_name}: {e}")
            return None

    def load_all_calibrations(self) -> Dict[str, float]:
        """Load all probe calibrations"""
        try:
            calibrations = self._load_all()
            return {name: data.get('offset_c', 0.0) for name, data in calibrations.items()}
        except Exception as e:
            logging.error(f"Failed to load calibrations: {e}")
            return {}

    def _load_all(self) -> Dict:
        """Load all calibrations from file"""
        try:
            if not self.config_file.exists():
                return {}

            with open(self.config_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logging.warning(f"Corrupted calibration file {self.config_file}, starting fresh")
            return {}
        except PermissionError:
            logging.warning(f"No permission to read calibration file {self.config_file}")
            return {}
        except Exception as e:
            logging.error(f"Error reading calibration file: {e}")
            return {}

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()


# Global persistence instance
calibration_persistence = CalibrationPersistence()
