"""Data structures for evaluating detections and counts.

Ground truth is kept separate from :class:`~aeronetra.detection.types.Detection`:
an annotated object has a class and a box but no confidence or model provenance.
"""

from collections.abc import Sequence
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
    """All annotations for one image.

    ``objects`` holds the objects that count toward metrics. ``ignored`` holds
    regions the dataset marks as not-to-be-evaluated (VisDrone ignored regions
    and rows with score ``0``): a detection falling inside one is neither a true
    positive nor a false positive, and an ignored region is never a false
    negative. Keeping them in a separate list means counting and per-class
    logic over ``objects`` stays correct without every caller re-filtering.
    """

    image_id: str
    objects: list[GroundTruthObject] = field(default_factory=list)
    ignored: list[GroundTruthObject] = field(default_factory=list)

    def ignore_boxes(self) -> list[BoundingBox]:
        """Return the boxes of the ignored regions for this image."""
        return [obj.box for obj in self.ignored]


@dataclass
class GroundTruth:
    """A keyed collection of annotated images."""

    images: dict[str, GroundTruthImage] = field(default_factory=dict)

    def add_image(
        self,
        image_id: str,
        objects: list[GroundTruthObject],
        ignored: list[GroundTruthObject] | None = None,
    ) -> None:
        """Add or replace the annotations for ``image_id``.

        Args:
            objects: Objects that count toward metrics.
            ignored: Regions excluded from evaluation (see
                :class:`GroundTruthImage`). Defaults to none.
        """
        self.images[image_id] = GroundTruthImage(image_id, objects, ignored or [])

    def class_ids(self) -> set[int]:
        """Return the set of class ids that appear in the annotations."""
        return {obj.class_id for image in self.images.values() for obj in image.objects}

    def counts_by_image(
        self,
        class_ids: Sequence[int] | set[int] | None = None,
    ) -> dict[str, int]:
        """Return annotated object counts per image, optionally by class."""
        allowed = None if class_ids is None else set(class_ids)
        return {
            image_id: sum(
                1
                for obj in image.objects
                if allowed is None or obj.class_id in allowed
            )
            for image_id, image in self.images.items()
        }

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
class StratumMetrics:
    """Detection metrics for one stratum: a size band or a density band."""

    name: str
    num_ground_truth: int
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1: float


@dataclass
class StratifiedMetrics:
    """Detection metrics broken down by object size and image density.

    Stratification answers *where* the errors are, not only how many there are.
    Both breakdowns use the same operating point as :class:`DetectionMetrics`,
    so their counts reconcile with the aggregate ones.
    """

    by_size: dict[str, StratumMetrics] = field(default_factory=dict)
    by_density: dict[str, StratumMetrics] = field(default_factory=dict)
    operating_confidence: float = 0.25
    match_iou: float = 0.5


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
    stratified: StratifiedMetrics | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable dict of the whole report."""
        return asdict(self)
