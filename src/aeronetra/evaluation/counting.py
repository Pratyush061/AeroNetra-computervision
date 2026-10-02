"""Count-error metrics for image-level vehicle counting."""

import math

from aeronetra.detection.types import ModelPrediction
from aeronetra.evaluation.types import CountMetrics, ImageCountError


def predicted_counts(
    predictions: dict[str, ModelPrediction], conf_threshold: float = 0.0
) -> dict[str, int]:
    """Return the number of surviving detections per image.

    Args:
        predictions: Standardised predictions keyed by image id.
        conf_threshold: Detections below this confidence are dropped first.
    """
    return {
        image_id: len(prediction.filter_by_confidence(conf_threshold).detections)
        for image_id, prediction in predictions.items()
    }


def evaluate_counting(predicted: dict[str, int], actual: dict[str, int]) -> CountMetrics:
    """Compare predicted per-image counts against actual counts.

    Images present in only one mapping are treated as having a count of zero on
    the missing side, so a missing or spurious image is a real error rather than
    being silently dropped.

    Args:
        predicted: Predicted vehicle count per image id.
        actual: Ground-truth vehicle count per image id.

    Returns:
        A :class:`CountMetrics` with MAE, RMSE, signed bias and MAPE.
    """
    image_ids = sorted(set(predicted) | set(actual))
    per_image: dict[str, ImageCountError] = {}
    errors: list[int] = []
    absolute_errors: list[int] = []
    for image_id in image_ids:
        pred = predicted.get(image_id, 0)
        act = actual.get(image_id, 0)
        error = pred - act
        per_image[image_id] = ImageCountError(image_id, pred, act, error, abs(error))
        errors.append(error)
        absolute_errors.append(abs(error))

    count = len(image_ids)
    mae = sum(absolute_errors) / count if count else 0.0
    rmse = math.sqrt(sum(e * e for e in errors) / count) if count else 0.0
    bias = sum(errors) / count if count else 0.0

    # MAPE is only defined where the actual count is non-zero.
    relative = [
        abs(predicted.get(image_id, 0) - actual[image_id]) / actual[image_id]
        for image_id in image_ids
        if actual.get(image_id, 0) > 0
    ]
    mape = 100.0 * sum(relative) / len(relative) if relative else 0.0

    return CountMetrics(
        num_images=count,
        total_predicted=sum(predicted.values()),
        total_actual=sum(actual.values()),
        mae=mae,
        rmse=rmse,
        bias=bias,
        mape=mape,
        per_image=per_image,
    )
