"""AeroNetra — UAV/drone-based vehicle detection and counting."""

__version__ = "0.1.0"

from aeronetra.detection.adapters import get_model_adapter
from aeronetra.detection.types import (
    BoundingBox,
    CountSummary,
    Detection,
    InferenceMetadata,
    ModelPrediction,
)

__all__ = [
    "BoundingBox",
    "CountSummary",
    "Detection",
    "InferenceMetadata",
    "ModelPrediction",
    "get_model_adapter",
]
