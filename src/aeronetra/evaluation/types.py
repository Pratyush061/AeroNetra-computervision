"""Data structures for evaluating detections and counts.

Ground truth is kept separate from :class:`~aeronetra.detection.types.Detection`:
an annotated object has a class and a box but no confidence or model provenance.
"""

from dataclasses import asdict, dataclass, field
from typing import Any

from aeronetra.detection.types import BoundingBox, InferenceMetadata


@dataclass(frozen=True)
class GroundTruthObject:
    """A single annotated object: a class id and an absolute xyxy box."""

    class_id: int
    box: BoundingBox


@dataclass
class GroundTruthImage:
    """All annotated objects for one image."""

    image_id: str
    objects: list[GroundTruthObject] = field(default_factory=list)


@dataclass
class GroundTruth:
    """A keyed collection of annotated images."""

    images: dict[str, GroundTruthImage] = field(default_factory=dict)

    def add_image(self, image_id: str, objects: list[GroundTruthObject]) -> None:
        """Add or replace the annotations for ``image_id``."""
        self.images[image_id] = GroundTruthImage(image_id, objects)

    def class_ids(self) -> set[int]:
        """Return the set of class ids that appear in the annotations."""
        return {obj.class_id for image in self.images.values() for obj in image.objects}

    def counts_by_image(self) -> dict[str, int]:
        """Return the number of annotated objects per image."""
        return {image_id: len(image.objects) for image_id, image in self.images.items()}

    def total_objects(self) -> int:
        """Return the total number of annotated objects."""
        return sum(len(image.objects) for image in self.images.values())


@dataclass
class MatchOutcome:
    """Result of matching detections to ground truths for a single image."""

    matched: list[tuple[int, int]] = field(default_factory=list)
    unmatched_detections: list[int] = field(default_factory=list)
    unmatched_ground_truths: list[int] = field(default_factory=list)


@dataclass
class ClassMetrics:
    """Detection metrics for a single class at the operating point."""

    class_id: int
    num_ground_truth: int
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1: float
    ap50: float
    ap50_95: float


@dataclass
class DetectionMetrics:
    """Aggregate detection metrics for a whole evaluation run."""

    precision: float
    recall: float
    f1: float
    map50: float
    map50_95: float
    num_ground_truth: int
    num_detections: int
    operating_confidence: float
    ap_confidence: float
    match_iou: float
    iou_thresholds: list[float]
    mean_inference_ms: float
    per_class: dict[int, ClassMetrics] = field(default_factory=dict)


@dataclass
class ImageCountError:
    """Predicted-versus-actual vehicle count for one image."""

    image_id: str
    predicted: int
    actual: int
    error: int
    absolute_error: int


@dataclass
class CountMetrics:
    """Count-error metrics across a set of images.

    ``bias`` is the mean signed error, so a positive value means the model
    over-counts on average.
    """

    num_images: int
    total_predicted: int
    total_actual: int
    mae: float
    rmse: float
    bias: float
    mape: float
    per_image: dict[str, ImageCountError] = field(default_factory=dict)


@dataclass
class EvaluationReport:
    """A complete, serialisable evaluation result for one model run."""

    detection: DetectionMetrics
    counting: CountMetrics
    metadata: InferenceMetadata | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable dict of the whole report."""
        return asdict(self)
