"""Unit tests for detection metrics (precision/recall and average precision)."""

import pytest

from aeronetra.detection.types import BoundingBox, Detection, ModelPrediction
from aeronetra.evaluation.detection import DEFAULT_AP_CONFIDENCE, evaluate_detection
from aeronetra.evaluation.types import GroundTruth, GroundTruthObject


def _ground_truth() -> GroundTruth:
    ground_truth = GroundTruth()
    ground_truth.add_image(
        "a",
        [
            GroundTruthObject(0, BoundingBox(0, 0, 10, 10)),
            GroundTruthObject(0, BoundingBox(20, 20, 30, 30)),
        ],
    )
    ground_truth.add_image("b", [GroundTruthObject(0, BoundingBox(0, 0, 10, 10))])
    return ground_truth


def _prediction(detections: list[Detection]) -> ModelPrediction:
    return ModelPrediction(detections=detections, image_width=100, image_height=100)


def _car(box: tuple[float, float, float, float], conf: float = 0.9) -> Detection:
    return Detection(BoundingBox(*box), 0, "car", conf)


def test_perfect_detections_score_one():
    predictions = {
        "a": _prediction([_car((0, 0, 10, 10)), _car((20, 20, 30, 30), 0.8)]),
        "b": _prediction([_car((0, 0, 10, 10))]),
    }

    metrics = evaluate_detection(predictions, _ground_truth())

    assert metrics.precision == 1.0
    assert metrics.recall == 1.0
    assert metrics.f1 == 1.0
    assert metrics.map50 == 1.0
    assert metrics.map50_95 == 1.0
    assert metrics.num_ground_truth == 3
    assert metrics.num_detections == 3


def test_misses_and_false_positives_reduce_metrics():
    predictions = {
        "a": _prediction([_car((0, 0, 10, 10))]),  # 1 TP, 1 FN
        "b": _prediction([_car((50, 50, 60, 60))]),  # 1 FP, 1 FN
    }

    metrics = evaluate_detection(predictions, _ground_truth())
    car = metrics.per_class[0]

    assert (car.true_positives, car.false_positives, car.false_negatives) == (1, 1, 2)
    assert metrics.precision == 0.5
    assert metrics.recall == 1 / 3
    assert 0.0 < metrics.map50 < 1.0


def test_empty_predictions_give_zero_detection_metrics():
    metrics = evaluate_detection({}, _ground_truth())

    assert metrics.recall == 0.0
    assert metrics.map50 == 0.0
    assert metrics.map50_95 == 0.0
    assert metrics.num_ground_truth == 3
    assert metrics.num_detections == 0


def test_confidence_threshold_drops_detections():
    predictions = {"a": _prediction([_car((0, 0, 10, 10), conf=0.1)])}

    metrics = evaluate_detection(predictions, _ground_truth(), conf_threshold=0.25)

    assert metrics.num_detections == 0


def test_predicted_only_class_is_excluded_from_map():
    predictions = {
        "a": _prediction(
            [
                _car((0, 0, 10, 10)),
                Detection(BoundingBox(90, 90, 99, 99), 5, "bus", 0.9),
            ]
        )
    }

    metrics = evaluate_detection(predictions, _ground_truth())

    # Class 5 has no ground truth: it is reported per-class but not averaged.
    assert metrics.per_class[5].num_ground_truth == 0
    assert metrics.map50 == metrics.per_class[0].ap50


def _single_car_ground_truth() -> GroundTruth:
    ground_truth = GroundTruth()
    ground_truth.add_image("a", [GroundTruthObject(0, BoundingBox(0, 0, 10, 10))])
    return ground_truth


def test_low_confidence_detection_contributes_to_map_not_operating_point():
    # A correct car below the operating threshold still earns average precision
    # (built at ap_conf_threshold) but not operating-point recall.
    predictions = {"a": _prediction([_car((0, 0, 10, 10), conf=0.1)])}

    metrics = evaluate_detection(predictions, _single_car_ground_truth())

    assert metrics.num_detections == 0  # the operating point sees nothing
    assert metrics.recall == 0.0
    assert metrics.map50 == 1.0  # AP still credits the detection
    assert metrics.ap_confidence == DEFAULT_AP_CONFIDENCE


def test_ap_confidence_threshold_can_exclude_low_confidence():
    predictions = {"a": _prediction([_car((0, 0, 10, 10), conf=0.1)])

    metrics = evaluate_detection(
        predictions, _single_car_ground_truth(), ap_conf_threshold=0.25
    )

    assert metrics.map50 == 0.0


def test_class_agnostic_mode_is_rejected_instead_of_returning_misleading_metrics():
    with pytest.raises(ValueError, match="only supports class-aware"):
        evaluate_detection(
            {"a": _prediction([_car((0, 0, 10, 10))])},
            _single_car_ground_truth(),
            class_aware=False,
        )
