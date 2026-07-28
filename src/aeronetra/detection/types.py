"""
Core data structures for object detection and counting.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Tuple

@dataclass
class BoundingBox:
    """Represents a bounding box in xyxy format (xmin, ymin, xmax, ymax)."""
    xmin: float
    ymin: float
    xmax: float
    ymax: float

    @property
    def xyxy(self) -> Tuple[float, float, float, float]:
        return (self.xmin, self.ymin, self.xmax, self.ymax)

    @property
    def width(self) -> float:
        return self.xmax - self.xmin

    @property
    def height(self) -> float:
        return self.ymax - self.ymin

    @property
    def area(self) -> float:
        return max(0.0, self.width) * max(0.0, self.height)

    @property
    def center(self) -> Tuple[float, float]:
        return (self.xmin + self.width / 2, self.ymin + self.height / 2)


@dataclass
class Detection:
    """Represents a single detected object."""
    box: BoundingBox
    class_id: int
    class_name: str
    confidence: float
    source_model: str = "unknown"
    image_id: str = "unknown"


@dataclass
class ModelPrediction:
    """Represents the complete set of detections from a model for one image."""
    detections: List[Detection] = field(default_factory=list)
    image_width: int = 0
    image_height: int = 0
    inference_time_ms: float = 0.0

    def filter_by_confidence(self, threshold: float):
        """Filters detections below confidence threshold."""
        self.detections = [d for d in self.detections if d.confidence >= threshold]

    def filter_by_class(self, allowed_classes: List[int]):
        """Filters detections to only keep allowed classes."""
        self.detections = [d for d in self.detections if d.class_id in allowed_classes]


@dataclass
class CountSummary:
    """Represents the counting results for an image."""
    image_id: str
    total_vehicles: int
    class_counts: Dict[str, int]
    model_name: str


@dataclass
class InferenceMetadata:
    """Metadata for an inference run to ensure reproducibility and tracking."""
    model_name: str
    package_version: str
    weights_path: str
    dataset_version: str
    image_size: Tuple[int, int]
    confidence_threshold: float
    iou_threshold: float
    seed: int
    device: str
    timing_ms: float = 0.0
