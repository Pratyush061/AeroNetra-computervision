"""Object detection adapters and data types."""

from aeronetra.detection.types import (
    BoundingBox,
    CountSummary,
    Detection,
    InferenceMetadata,
    ModelPrediction,
)
from aeronetra.detection.adapters import BaseDetector, get_model_adapter

__all__ = [
    "BaseDetector",
    "BoundingBox",
    "CountSummary",
    "Detection",
    "InferenceMetadata",
    "ModelPrediction",
    "get_model_adapter",
]
