"""Unit tests for count-error metrics."""

from aeronetra.detection.types import BoundingBox, Detection, ModelPrediction
from aeronetra.evaluation.counting import evaluate_counting, predicted_counts


def test_predicted_counts_respects_threshold():
    predictions = {
        "a": ModelPrediction(
            detections=[
                Detection(BoundingBox(0, 0, 1, 1), 0, "car", 0.9),
                Detection(BoundingBox(0, 0, 1, 1), 0, "car", 0.2),
            ]
        )
    }

    assert predicted_counts(predictions) == {"a": 2}
    assert predicted_counts(predictions, conf_threshold=0.5) == {"a": 1}


def test_count_metrics_basic():
    metrics = evaluate_counting({"a": 3, "b": 1}, {"a": 2, "b": 2})

    assert metrics.num_images == 2
    assert metrics.total_predicted == 4
    assert metrics.total_actual == 4
    assert metrics.mae == 1.0
    assert metrics.rmse == 1.0
    assert metrics.bias == 0.0
    assert metrics.per_image["a"].error == 1
    assert metrics.per_image["b"].absolute_error == 1


def test_count_metrics_handle_missing_images_and_zero_actuals():
    metrics = evaluate_counting({"a": 1}, {"b": 0})

    assert metrics.num_images == 2
    assert metrics.per_image["a"].error == 1
    assert metrics.per_image["b"].error == 0
    assert metrics.mae == 0.5
    # Zero actual counts carry no meaningful percentage error.
    assert metrics.mape == 0.0


def test_mape_uses_nonzero_actuals():
    metrics = evaluate_counting({"a": 2}, {"a": 1})

    assert metrics.mape == 100.0
    assert metrics.bias == 1.0


def test_predicted_counts_filters_by_class():
    predictions = {
        "a": ModelPrediction(
            detections=[
                Detection(BoundingBox(0, 0, 1, 1), 0, "car", 0.9),
                Detection(BoundingBox(0, 0, 1, 1), 1, "van", 0.9),
                Detection(BoundingBox(0, 0, 1, 1), 5, "bus", 0.9),
            ]
        )
    }

    assert predicted_counts(predictions) == {"a": 3}
    assert predicted_counts(predictions, class_ids={0, 1}) == {"a": 2}
    assert predicted_counts(predictions, class_ids=[5]) == {"a": 1}
