"""Object detection adapters and data types."""

from aeronetra.detection.adapters import (
    BaseDetector,
    OnnxRuntimeAdapter,
    UltralyticsAdapter,
    get_model_adapter,
)
from aeronetra.detection.types import (
    BoundingBox,
    CountSummary,
    Detection,
    InferenceMetadata,
    ModelPrediction,
)

__all__ = [
    "BaseDetector",
    "BoundingBox",
    "CountSummary",
    "Detection",
    "InferenceMetadata",
    "ModelPrediction",
    "OnnxRuntimeAdapter",
    "UltralyticsAdapter",
    "get_model_adapter",
]
