"""Assemble detection and counting metrics into a single report."""

import json
from collections.abc import Sequence
from pathlib import Path

from aeronetra.detection.types import InferenceMetadata, ModelPrediction
from aeronetra.evaluation.counting import evaluate_counting, predicted_counts
from aeronetra.evaluation.detection import (
    DEFAULT_AP_CONFIDENCE,
    DEFAULT_IOU_THRESHOLDS,
    evaluate_detection,
)
from aeronetra.evaluation.types import EvaluationReport, GroundTruth
from aeronetra.utils.paths import ensure_dir


def evaluate_all(
    predictions: dict[str, ModelPrediction],
    ground_truth: GroundTruth,
    metadata: InferenceMetadata | None = None,
    conf_threshold: float = 0.25,
    ap_conf_threshold: float = DEFAULT_AP_CONFIDENCE,
    iou_thresholds: Sequence[float] = DEFAULT_IOU_THRESHOLDS,
    class_aware: bool = True,
    count_class_ids: Sequence[int] | set[int] | None = None,
) -> EvaluationReport:
    """Run detection and counting evaluation and return one report.

    Counting uses the same confidence threshold as the detection operating
    point, so both halves of the report describe one operating point. Average
    precision uses ``ap_conf_threshold`` instead, so mAP is not truncated.

    Args:
        count_class_ids: If given, restrict counting to these class ids on both
            predictions and ground truth, so the reported count errors compare
            like-for-like object sets. Detection metrics are unaffected.
    """
    detection = evaluate_detection(
        predictions,
        ground_truth,
        iou_thresholds=iou_thresholds,
        conf_threshold=conf_threshold,
        ap_conf_threshold=ap_conf_threshold,
        class_aware=class_aware,
    )
    counting = evaluate_counting(
        predicted_counts(predictions, conf_threshold, count_class_ids),
        ground_truth.counts_by_image(count_class_ids),
    )
    return EvaluationReport(detection=detection, counting=counting, metadata=metadata)


def save_report(report: EvaluationReport, output_path: Path) -> None:
    """Write a report to ``output_path`` as indented JSON."""
    ensure_dir(output_path.parent)
    output_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
