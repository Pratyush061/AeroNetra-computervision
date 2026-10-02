"""Unit tests for stratified (object size and image density) metrics."""

import pytest

from aeronetra.detection.types import BoundingBox, Detection, ModelPrediction
from aeronetra.evaluation import evaluate_all, evaluate_detection
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


def _detection(box: BoundingBox, confidence: float = 0.9, class_id: int = 0) -> Detection:
    return Detection(
        box=box, class_id=class_id, class_name="car", confidence=confidence
    )


def test_size_stratum_bands():
    assert size_stratum(BoundingBox(0, 0, 10, 10)) == "small"  # area 100
    assert size_stratum(BoundingBox(0, 0, 40, 40)) == "medium"  # area 1600
    assert size_stratum(BoundingBox(0, 0, 100, 100)) == "large"  # area 10000
    assert DEFAULT_SIZE_BOUNDS == (32.0**2, 96.0**2)


def test_size_stratum_boundaries_are_inclusive_lower():
    # COCO bands: small is area < 32**2, so exactly 32**2 already counts as medium.
    assert size_stratum(BoundingBox(0, 0, 32, 32)) == "medium"
    assert size_stratum(BoundingBox(0, 0, 96, 96)) == "large"


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


def test_multi_class_detection_does_not_match_across_classes():
    ground_truth = GroundTruth()
    ground_truth.add_image("a", [GroundTruthObject(0, SMALL_BOX)])

    # Identical box, but a different class: class-aware matching must not pair them.
    predictions = {"a": ModelPrediction([_detection(SMALL_BOX, class_id=1)])}

    report = evaluate_by_stratum(predictions, ground_truth)

    small = report.by_size["small"]
    assert (small.true_positives, small.false_positives, small.false_negatives) == (
        0,
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


def test_empty_inputs_return_zeroed_bands():
    report = evaluate_by_stratum({}, GroundTruth())

    assert set(report.by_size) == {"small", "medium", "large"}
    assert set(report.by_density) == {"sparse", "moderate", "dense", "very_dense"}
    for metrics in (*report.by_size.values(), *report.by_density.values()):
        assert metrics.num_ground_truth == 0
        assert metrics.precision == 0.0
        assert metrics.recall == 0.0


def test_rejects_class_agnostic_evaluation():
    ground_truth = GroundTruth()
    ground_truth.add_image("a", [GroundTruthObject(0, SMALL_BOX)])

    with pytest.raises(ValueError, match="only supports class-aware"):
        evaluate_by_stratum({"a": ModelPrediction([])}, ground_truth, class_aware=False)


def test_rejects_bounds_that_cannot_partition_the_labels():
    ground_truth = GroundTruth()

    with pytest.raises(ValueError, match="size_bounds must have exactly 2 boundary"):
        evaluate_by_stratum({}, ground_truth, size_bounds=(100.0,))

    with pytest.raises(ValueError, match="must be strictly positive"):
        evaluate_by_stratum({}, ground_truth, size_bounds=(0.0, 1000.0))

    with pytest.raises(ValueError, match="must be strictly ascending"):
        evaluate_by_stratum({}, ground_truth, size_bounds=(2000.0, 1000.0))

    with pytest.raises(ValueError, match="density_bounds must have exactly 3 boundary"):
        evaluate_by_stratum({}, ground_truth, density_bounds=(10,))


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


def test_evaluate_all_can_include_strata_in_the_report():
    ground_truth = GroundTruth()
    ground_truth.add_image("a", [GroundTruthObject(0, SMALL_BOX)])
    predictions = {"a": ModelPrediction([_detection(SMALL_BOX)])}

    assert evaluate_all(predictions, ground_truth).stratified is None

    report = evaluate_all(predictions, ground_truth, include_strata=True)

    assert report.stratified is not None
    assert report.stratified.by_size["small"].true_positives == 1
    # The breakdown survives serialisation, so save_report can persist it.
    serialised = report.to_dict()["stratified"]
    assert serialised["by_density"]["sparse"]["true_positives"] == 1
