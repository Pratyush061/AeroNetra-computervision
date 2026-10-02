"""Stratified detection metrics: where errors live, by size and density.

Aggregate precision and recall hide structure. A model can look adequate overall
while failing almost entirely on the tiny, densely packed objects that dominate
aerial imagery, so a single number is a poor description of it. This module
re-uses the package's matching at the same operating point and reports the
metrics per stratum instead.

Only strata derivable from boxes are computed here — object size and image
density — so no change to the ground-truth schema is required. Occlusion and
other annotated attributes can be added once they are carried on
:class:`~aeronetra.evaluation.types.GroundTruthObject`.
"""

from collections.abc import Sequence

from aeronetra.detection.types import BoundingBox, ModelPrediction
from aeronetra.evaluation.detection import OPERATING_IOU, _safe_ratio
from aeronetra.evaluation.matching import match_image
from aeronetra.evaluation.types import GroundTruth, StratifiedMetrics, StratumMetrics

# ``_safe_ratio`` is imported from ``detection`` rather than redefined here, so
# the metric division convention has exactly one definition in the package.

# COCO's absolute-area convention, in square pixels: < 32**2 is "small",
# < 96**2 is "medium", otherwise "large". Absolute rather than relative area
# keeps the bands comparable with published AP_small / AP_medium / AP_large.
DEFAULT_SIZE_BOUNDS: tuple[float, ...] = (32.0**2, 96.0**2)
SIZE_LABELS: tuple[str, ...] = ("small", "medium", "large")

# Annotated objects per image. The first band includes images with no
# annotations, so false positives on empty images are still counted.
DEFAULT_DENSITY_BOUNDS: tuple[int, ...] = (10, 50, 100)
DENSITY_LABELS: tuple[str, ...] = ("sparse", "moderate", "dense", "very_dense")


def _check_bounds(bounds: Sequence[float], labels: Sequence[str], name: str) -> None:
    """Reject a bound sequence that cannot partition the fixed ``labels``.

    The labels are fixed tuples, so bounds of the wrong length would silently
    collapse or drop bands, and non-ascending bounds would misassign boxes.
    Failing loudly keeps a bad configuration from producing quietly wrong strata.
    """
    if len(bounds) != len(labels) - 1:
        raise ValueError(
            f"{name} must have exactly {len(labels) - 1} boundary values to "
            f"partition {list(labels)}, got {len(bounds)}: {tuple(bounds)}"
        )
    if any(bound <= 0 for bound in bounds):
        raise ValueError(
            f"{name} values must be strictly positive, got {tuple(bounds)}"
        )
    if any(current >= following for current, following in zip(bounds, bounds[1:])):
        raise ValueError(f"{name} must be strictly ascending, got {tuple(bounds)}")


def size_stratum(box: BoundingBox, bounds: Sequence[float] = DEFAULT_SIZE_BOUNDS) -> str:
    """Return the size band for a box, measured by absolute pixel area.

    Args:
        box: An absolute ``xyxy`` box.
        bounds: Ascending, strictly positive upper area bounds; there must be
            one fewer bound than labels in :data:`SIZE_LABELS`.

    Returns:
        A label from :data:`SIZE_LABELS`.

    Raises:
        ValueError: If ``bounds`` cannot partition :data:`SIZE_LABELS`.
    """
    _check_bounds(bounds, SIZE_LABELS, "size_bounds")
    for bound, label in zip(bounds, SIZE_LABELS):
        if box.area < bound:
            return label
    return SIZE_LABELS[-1]


def density_stratum(count: int, bounds: Sequence[int] = DEFAULT_DENSITY_BOUNDS) -> str:
    """Return the density band for an image with ``count`` annotated objects.

    Args:
        count: Number of annotated objects in the image.
        bounds: Ascending, strictly positive inclusive upper bounds; there must
            be one fewer bound than labels in :data:`DENSITY_LABELS`.

    Returns:
        A label from :data:`DENSITY_LABELS`.

    Raises:
        ValueError: If ``bounds`` cannot partition :data:`DENSITY_LABELS`.
    """
    _check_bounds(bounds, DENSITY_LABELS, "density_bounds")
    for bound, label in zip(bounds, DENSITY_LABELS):
        if count <= bound:
            return label
    return DENSITY_LABELS[-1]


def _summarise(
    counts: dict[str, list[int]], gt_totals: dict[str, int]
) -> dict[str, StratumMetrics]:
    """Turn per-stratum ``[tp, fp, fn]`` tallies into metric objects."""
    strata: dict[str, StratumMetrics] = {}
    for label, (true_positives, false_positives, false_negatives) in counts.items():
        precision = _safe_ratio(true_positives, true_positives + false_positives)
        recall = _safe_ratio(true_positives, true_positives + false_negatives)
        strata[label] = StratumMetrics(
            name=label,
            num_ground_truth=gt_totals[label],
            true_positives=true_positives,
            false_positives=false_positives,
            false_negatives=false_negatives,
            precision=precision,
            recall=recall,
            f1=_safe_ratio(2 * precision * recall, precision + recall),
        )
    return strata


def evaluate_by_stratum(
    predictions: dict[str, ModelPrediction],
    ground_truth: GroundTruth,
    conf_threshold: float = 0.25,
    size_bounds: Sequence[float] = DEFAULT_SIZE_BOUNDS,
    density_bounds: Sequence[int] = DEFAULT_DENSITY_BOUNDS,
    class_aware: bool = True,
) -> StratifiedMetrics:
    """Break detection metrics down by object size and image density.

    The same operating point is used as
    :func:`~aeronetra.evaluation.detection.evaluate_detection` (IoU
    :data:`~aeronetra.evaluation.detection.OPERATING_IOU` and ``conf_threshold``),
    so the per-stratum counts sum back to the aggregate ones.

    Object-size strata attribute a matched pair to the *ground-truth* box and a
    false positive to the *detection* box. Image-density strata bin whole images
    by their annotated object count, so each image contributes all of its true
    positives, false positives and false negatives to one band. Every configured
    band is always present, so a band with no objects is reported with zero
    support rather than omitted.

    Args:
        predictions: Standardised predictions keyed by image id.
        ground_truth: Annotated objects keyed by image id.
        conf_threshold: Confidence threshold for the operating point.
        size_bounds: Upper area bounds for the size bands.
        density_bounds: Inclusive upper bounds for the density bands.
        class_aware: Must remain true, so the strata stay comparable with
            :func:`~aeronetra.evaluation.detection.evaluate_detection`, which
            rejects class-agnostic aggregation for the same reason.

    Returns:
        A :class:`StratifiedMetrics` with one breakdown per stratification.

    Raises:
        ValueError: If ``class_aware`` is false, or either bound sequence cannot
            partition its labels.
    """
    if not class_aware:
        raise ValueError(
            "evaluate_by_stratum only supports class-aware evaluation; "
            "class_agnostic aggregation requires a different metric schema"
        )
    # Validate up front so an invalid configuration fails even when there is no
    # data to stratify.
    _check_bounds(size_bounds, SIZE_LABELS, "size_bounds")
    _check_bounds(density_bounds, DENSITY_LABELS, "density_bounds")

    operating = {
        image_id: prediction.filter_by_confidence(conf_threshold)
        for image_id, prediction in predictions.items()
    }

    size_counts = {label: [0, 0, 0] for label in SIZE_LABELS}
    size_gt = {label: 0 for label in SIZE_LABELS}
    density_counts = {label: [0, 0, 0] for label in DENSITY_LABELS}
    density_gt = {label: 0 for label in DENSITY_LABELS}

    for image_id in set(ground_truth.images) | set(operating):
        gt_image = ground_truth.images.get(image_id)
        gt_objects = gt_image.objects if gt_image is not None else []
        prediction = operating.get(image_id)
        detections = prediction.detections if prediction is not None else []

        outcome = match_image(detections, gt_objects, OPERATING_IOU, class_aware)
        density_label = density_stratum(len(gt_objects), density_bounds)
        density_gt[density_label] += len(gt_objects)

        for _, gt_index in outcome.matched:
            label = size_stratum(gt_objects[gt_index].box, size_bounds)
            size_counts[label][0] += 1
            size_gt[label] += 1
            density_counts[density_label][0] += 1

        for gt_index in outcome.unmatched_ground_truths:
            label = size_stratum(gt_objects[gt_index].box, size_bounds)
            size_counts[label][2] += 1
            size_gt[label] += 1
            density_counts[density_label][2] += 1

        for det_index in outcome.unmatched_detections:
            label = size_stratum(detections[det_index].box, size_bounds)
            size_counts[label][1] += 1
            density_counts[density_label][1] += 1

    return StratifiedMetrics(
        by_size=_summarise(size_counts, size_gt),
        by_density=_summarise(density_counts, density_gt),
        operating_confidence=conf_threshold,
        match_iou=OPERATING_IOU,
    )
