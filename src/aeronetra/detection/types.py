"""Core data structures for object detection and counting."""

from dataclasses import dataclass, field


@dataclass
class BoundingBox:
    """Represents a bounding box in xyxy format (xmin, ymin, xmax, ymax)."""

    xmin: float
    ymin: float
    xmax: float
    ymax: float

    def __post_init__(self):
        """Validate that coordinates form a valid box."""
        if self.xmin > self.xmax:
            raise ValueError(
                f"Invalid BoundingBox: xmin ({self.xmin}) > xmax ({self.xmax})"
            )
        if self.ymin > self.ymax:
            raise ValueError(
                f"Invalid BoundingBox: ymin ({self.ymin}) > ymax ({self.ymax})"
            )

    @property
    def xyxy(self) -> tuple[float, float, float, float]:
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
    def center(self) -> tuple[float, float]:
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

    detections: list[Detection] = field(default_factory=list)
    image_width: int = 0
    image_height: int = 0
    inference_time_ms: float = 0.0

    def filter_by_confidence(self, threshold: float) -> "ModelPrediction":
        """Returns a new ModelPrediction with detections above the threshold."""
        filtered = [d for d in self.detections if d.confidence >= threshold]
        return ModelPrediction(
            detections=filtered,
            image_width=self.image_width,
            image_height=self.image_height,
            inference_time_ms=self.inference_time_ms,
        )

    def filter_by_class(self, allowed_classes: list[int]) -> "ModelPrediction":
        """Returns a new ModelPrediction with only the allowed class IDs."""
        filtered = [d for d in self.detections if d.class_id in allowed_classes]
        return ModelPrediction(
            detections=filtered,
            image_width=self.image_width,
            image_height=self.image_height,
            inference_time_ms=self.inference_time_ms,
        )


@dataclass
class CountSummary:
    """Represents the counting results for an image."""

    image_id: str
    total_vehicles: int
    class_counts: dict[str, int]
    model_name: str


@dataclass
class InferenceMetadata:
    """Metadata for an inference run to ensure reproducibility and tracking."""

    model_name: str
    package_version: str
    weights_path: str
    dataset_version: str
    image_size: tuple[int, int]
    confidence_threshold: float
    iou_threshold: float
    seed: int
    device: str
    timing_ms: float = 0.0
