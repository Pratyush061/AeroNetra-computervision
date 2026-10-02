"""Unit tests for stratified (object size and image density) metrics."""

from aeronetra.detection.types import BoundingBox, Detection, ModelPrediction
from aeronetra.evaluation.detection import evaluate_detection
from aeronetra.evaluation.strata import (
    DEFAULT_DENSITY_BOUNDS,
    DEFAULT_SIZE_BOUNDS,
    density_stratum,
    evaluate_by_stratum,
    size_stratum,
)
from aeronetra.evaluation.types import GroundTruth, GroundTruthObject

SMALL_BOX = BoundingBox(10, 10, 20, 20)  # area 100 -> small
LARGE_BOX = BoundingBox(0, 0, 200, 200)  # area 40000 -> large


def _detection(box: BoundingBox, confidence: float = 0.9) -> Detection:
    return Detection(
        box=box, class_id=0, class_name="car", confidence=confidence
    )


def test_size_stratum_bands():
    assert size_stratum(BoundingBox(0, 0, 10, 10)) == "small"  # area 100
    assert size_stratum(BoundingBox(0, 0, 40, 40)) == "medium"  # area 1600
    assert size_stratum(BoundingBox(0, 0, 100, 100)) == "large"  # area 10000
    assert DEFAULT_SIZE_BOUNDS == (32.0**2, 96.0**2)


def test_density_stratum_bands():
    assert density_stratum(0) == "sparse"
    assert density_stratum(10) == "sparse"
    assert density_stratum(11) == "moderate"
    assert density_stratum(50) == "moderate"
    assert density_stratum(51) == "dense"
    assert density_stratum(100) == "dense"
    assert density_stratum(101) == "very_dense"
    assert DEFAULT_DENSITY_BOUNDS == (10, 50, 100)


def test_evaluate_by_stratum_attributes_errors_to_size_and_density():
    ground_truth = GroundTruth()
    ground_truth.add_image(
        "a",
        [GroundTruthObject(0, SMALL_BOX), GroundTruthObject(0, LARGE_BOX)],
    )

    # The small car is found; the large one is missed; one small false positive.
    predictions = {
        "a": ModelPrediction(
            [_detection(SMALL_BOX), _detection(BoundingBox(500, 500, 510, 510))]
        )
    }

    report = evaluate_by_stratum(predictions, ground_truth)

    small = report.by_size["small"]
    assert (small.true_positives, small.false_positives, small.false_negatives) == (
        1,
        1,
        0,
    )
    assert small.precision == 0.5
    assert small.recall == 1.0

    large = report.by_size["large"]
    assert (large.true_positives, large.false_positives, large.false_negatives) == (
        0,
        0,
        1,
    )
    assert large.recall == 0.0
    assert large.num_ground_truth == 1

    # Two annotated objects -> the sparse density band.
    sparse = report.by_density["sparse"]
    assert (sparse.true_positives, sparse.false_positives, sparse.false_negatives) == (
        1,
        1,
        1,
    )


def test_missing_predictions_become_false_negatives():
    ground_truth = GroundTruth()
    ground_truth.add_image("a", [GroundTruthObject(0, SMALL_BOX)])

    report = evaluate_by_stratum({}, ground_truth)

    small = report.by_size["small"]
    assert small.false_negatives == 1
    assert small.true_positives == 0
    assert small.recall == 0.0


def test_false_positives_on_empty_images_are_counted():
    ground_truth = GroundTruth()
    ground_truth.add_image("a", [])  # annotated, but empty

    predictions = {"a": ModelPrediction([_detection(SMALL_BOX)])}

    report = evaluate_by_stratum(predictions, ground_truth)

    assert report.by_size["small"].false_positives == 1
    # An empty image falls in the first density band so its FP is not dropped.
    assert report.by_density["sparse"].false_positives == 1


def test_strata_totals_reconcile_with_aggregate_metrics():
    ground_truth = GroundTruth()
    ground_truth.add_image(
        "a",
        [GroundTruthObject(0, SMALL_BOX), GroundTruthObject(0, LARGE_BOX)],
    )
    ground_truth.add_image("b", [GroundTruthObject(0, SMALL_BOX)])

    predictions = {
        "a": ModelPrediction(
            [_detection(SMALL_BOX), _detection(BoundingBox(500, 500, 510, 510))]
        ),
        "b": ModelPrediction([_detection(SMALL_BOX)]),
    }

    aggregate = evaluate_detection(predictions, ground_truth)
    strata = evaluate_by_stratum(predictions, ground_truth)

    expected = {
        key: sum(getattr(metrics, key) for metrics in aggregate.per_class.values())
        for key in ("true_positives", "false_positives", "false_negatives")
    }

    for field in ("true_positives", "false_positives", "false_negatives"):
        by_size = sum(getattr(s, field) for s in strata.by_size.values())
        by_density = sum(getattr(s, field) for s in strata.by_density.values())
        assert by_size == expected[field]
        assert by_density == expected[field]
