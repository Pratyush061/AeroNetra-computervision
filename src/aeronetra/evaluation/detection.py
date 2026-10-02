"""Detection metrics: precision/recall and COCO-style average precision."""

import bisect
from collections.abc import Sequence

from aeronetra.detection.types import Detection, ModelPrediction
from aeronetra.evaluation.matching import match_image
from aeronetra.evaluation.types import (
    ClassMetrics,
    DetectionMetrics,
    GroundTruth,
    GroundTruthObject,
)

# COCO's standard IoU sweep for mAP@50-95.
DEFAULT_IOU_THRESHOLDS: tuple[float, ...] = tuple(
    round(0.5 + 0.05 * i, 2) for i in range(10)
)
# The single IoU used for the reported precision/recall/f1 operating point.
OPERATING_IOU = 0.5
# Average precision is built from near-all detections, so it is not truncated by
# the (higher) operating-point threshold. A small floor keeps zero-confidence
# rows out without changing the curve.
DEFAULT_AP_CONFIDENCE = 0.001


def _safe_ratio(numerator: float, denominator: float) -> float:
    """Divide, returning 0.0 when the denominator is zero."""
    return numerator / denominator if denominator > 0 else 0.0


def _group_by_image(
    detections: list[tuple[str, Detection]],
) -> dict[str, list[Detection]]:
    """Group ``(image_id, detection)`` pairs into per-image detection lists."""
    grouped: dict[str, list[Detection]] = {}
    for image_id, detection in detections:
        grouped.setdefault(image_id, []).append(detection)
    return grouped


def _average_precision(
    detections: list[tuple[str, Detection]],
    gt_by_image: dict[str, list[GroundTruthObject]],
    iou_threshold: float,
    class_aware: bool,
) -> float:
    """101-point interpolated average precision for one class at one IoU.

    Args:
        detections: ``(image_id, detection)`` pairs for the class.
        gt_by_image: Ground-truth objects of the class, keyed by image id.
        iou_threshold: IoU used to decide a true positive.
        class_aware: Whether matching must respect class id.

    Returns:
        Average precision in ``[0, 1]``; 0.0 when the class has no ground truth.
    """
    num_gt = sum(len(objects) for objects in gt_by_image.values())
    if num_gt == 0:
        return 0.0

    grouped = _group_by_image(detections)

    # (confidence, is_true_positive) for every detection, across all images.
    records: list[tuple[float, bool]] = []
    for image_id, image_detections in grouped.items():
        outcome = match_image(
            image_detections, gt_by_image.get(image_id, []), iou_threshold, class_aware
        )
        true_positives = {det_index for det_index, _ in outcome.matched}
        records.extend(
            (detection.confidence, index in true_positives)
            for index, detection in enumerate(image_detections)
        )

    records.sort(key=lambda record: record[0], reverse=True)
    precisions: list[float] = []
    recalls: list[float] = []
    tp = 0
    fp = 0
    for _, is_true_positive in records:
        tp += is_true_positive
        fp += not is_true_positive
        precisions.append(tp / (tp + fp))
        recalls.append(tp / num_gt)

    # Precision envelope so precision is non-increasing as recall grows.
    for i in range(len(precisions) - 2, -1, -1):
        precisions[i] = max(precisions[i], precisions[i + 1])

    total = 0.0
    for step in range(101):
        recall_level = step / 100.0
        index = bisect.bisect_left(recalls, recall_level)
        total += precisions[index] if index < len(precisions) else 0.0
    return total / 101.0


def _operating_point(
    detections: list[tuple[str, Detection]],
    gt_by_image: dict[str, list[GroundTruthObject]],
    iou_threshold: float,
    class_aware: bool,
) -> tuple[int, int, int]:
    """Return micro (true positives, false positives, false negatives) for a class."""
    grouped = _group_by_image(detections)

    tp = fp = fn = 0
    for image_id, image_detections in grouped.items():
        outcome = match_image(
            image_detections, gt_by_image.get(image_id, []), iou_threshold, class_aware
        )
        tp += len(outcome.matched)
        fp += len(outcome.unmatched_detections)
        fn += len(outcome.unmatched_ground_truths)

    # Images with annotations but no detections still contribute false negatives.
    for image_id, objects in gt_by_image.items():
        if image_id not in grouped:
            fn += len(objects)
    return tp, fp, fn


def evaluate_detection(
    predictions: dict[str, ModelPrediction],
    ground_truth: GroundTruth,
    iou_thresholds: Sequence[float] = DEFAULT_IOU_THRESHOLDS,
    conf_threshold: float = 0.25,
    ap_conf_threshold: float = DEFAULT_AP_CONFIDENCE,
    class_aware: bool = True,
) -> DetectionMetrics:
    """Evaluate detections against ground truth.

    Two confidence thresholds are used deliberately, mirroring COCO:

    * ``ap_conf_threshold`` (low) selects the detections that build the
      precision/recall curve, so mAP is not truncated by the operating point.
    * ``conf_threshold`` (higher) is the operating point reported as
      precision/recall/F1 and reported in ``num_detections``. Counting should
      use the same threshold.

    Args:
        predictions: Standardised predictions keyed by image id.
        ground_truth: Annotated objects keyed by image id.
        iou_thresholds: IoU values averaged to produce mAP@50-95.
        conf_threshold: Confidence threshold for the operating point.
        ap_conf_threshold: Confidence floor for the average-precision curve.
        class_aware: Require a class match when pairing boxes.

    Returns:
        A :class:`DetectionMetrics` holding the operating-point precision,
        recall and F1, per-class metrics, and mAP@50 / mAP@50-95. Only classes
        that have ground truth contribute to the two mAP figures.
    """
    operating = {
        image_id: prediction.filter_by_confidence(conf_threshold)
        for image_id, prediction in predictions.items()
    }
    for_ap = {
        image_id: prediction.filter_by_confidence(ap_conf_threshold)
        for image_id, prediction in predictions.items()
    }

    predicted_classes = {d.class_id for p in operating.values() for d in p.detections}
    all_classes = sorted(ground_truth.class_ids() | predicted_classes)
    thresholds = list(iou_thresholds)

    per_class: dict[int, ClassMetrics] = {}
    total_tp = total_fp = total_fn = 0
    ap50_values: list[float] = []
    ap50_95_values: list[float] = []

    for class_id in all_classes:
        gt_by_image = {
            image_id: [o for o in image.objects if o.class_id == class_id]
            for image_id, image in ground_truth.images.items()
        }
        operating_detections = [
            (image_id, d)
            for image_id, p in operating.items()
            for d in p.detections
            if d.class_id == class_id
        ]
        ap_detections = [
            (image_id, d)
            for image_id, p in for_ap.items()
            for d in p.detections
            if d.class_id == class_id
        ]
        num_gt = sum(len(objects) for objects in gt_by_image.values())

        tp, fp, fn = _operating_point(
            operating_detections, gt_by_image, OPERATING_IOU, class_aware
        )
        precision = _safe_ratio(tp, tp + fp)
        recall = _safe_ratio(tp, tp + fn)
        f1 = _safe_ratio(2 * precision * recall, precision + recall)
        ap50 = _average_precision(ap_detections, gt_by_image, OPERATING_IOU, class_aware)
        ap50_95 = (
            sum(
                _average_precision(ap_detections, gt_by_image, t, class_aware)
                for t in thresholds
            )
            / len(thresholds)
            if thresholds
            else 0.0
        )

        per_class[class_id] = ClassMetrics(
            class_id=class_id,
            num_ground_truth=num_gt,
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            precision=precision,
            recall=recall,
            f1=f1,
            ap50=ap50,
            ap50_95=ap50_95,
        )
        total_tp += tp
        total_fp += fp
        total_fn += fn
        if num_gt > 0:
            ap50_values.append(ap50)
            ap50_95_values.append(ap50_95)

    inference_times = [
        p.inference_time_ms for p in predictions.values() if p.inference_time_ms > 0
    ]

    return DetectionMetrics(
        precision=_safe_ratio(total_tp, total_tp + total_fp),
        recall=_safe_ratio(total_tp, total_tp + total_fn),
        f1=_safe_ratio(2 * total_tp, 2 * total_tp + total_fp + total_fn),
        map50=sum(ap50_values) / len(ap50_values) if ap50_values else 0.0,
        map50_95=sum(ap50_95_values) / len(ap50_95_values) if ap50_95_values else 0.0,
        num_ground_truth=ground_truth.total_objects(),
        num_detections=sum(len(p.detections) for p in operating.values()),
        operating_confidence=conf_threshold,
        ap_confidence=ap_conf_threshold,
        match_iou=OPERATING_IOU,
        iou_thresholds=thresholds,
        mean_inference_ms=(
            sum(inference_times) / len(inference_times) if inference_times else 0.0
        ),
        per_class=per_class,
    )
