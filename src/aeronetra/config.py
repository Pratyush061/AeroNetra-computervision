"""Configuration management for AeroNetra."""
import os
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"

# Model constants
DEFAULT_CONFIDENCE = 0.5
DEFAULT_IOU = 0.45

def get_data_dir() -> Path:
    """Get the base data directory."""
    return Path(os.environ.get("DATASET_DIR", RAW_DATA_DIR))
