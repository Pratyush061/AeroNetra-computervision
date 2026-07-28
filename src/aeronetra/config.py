"""Configuration management for AeroNetra."""

import os
from pathlib import Path
from typing import Any

import yaml

# ── Directory layout ───────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
OUTPUT_DIR = ROOT_DIR / "outputs"
CONFIGS_DIR = ROOT_DIR / "configs"

# ── Default thresholds ────────────────────────────────────────────────────
# NOTE: inference.yaml uses confidence_threshold=0.25.
# YAML values are authoritative at runtime; these are fallbacks only.
DEFAULT_CONFIDENCE = 0.5
DEFAULT_IOU = 0.45


def get_data_dir() -> Path:
    """Return the base data directory, respecting DATASET_DIR env var."""
    return Path(os.environ.get("DATASET_DIR", str(RAW_DATA_DIR)))


def get_output_dir() -> Path:
    """Return the output directory, respecting OUTPUT_DIR env var."""
    return Path(os.environ.get("OUTPUT_DIR", str(OUTPUT_DIR)))


def load_yaml(config_path: Path) -> dict[str, Any]:
    """Load a YAML configuration file and return its contents as a dict.

    Raises:
        FileNotFoundError: If the config file does not exist.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_inference_config() -> dict[str, Any]:
    """Load the shared inference config from configs/inference/inference.yaml."""
    return load_yaml(CONFIGS_DIR / "inference" / "inference.yaml")
