"""Assemble detection and counting metrics into a single report."""

import json
from collections.abc import Sequence
from pathlib import Path

from aeronetra.detection.types import InferenceMetadata, ModelPrediction
from aeronetra.evaluation.counting import evaluate_counting, predicted_counts
from aeronetra.evaluation.detection import DEFAULT_IOU_THRESHOLDS, evaluate_detection
from aeronetra.evaluation.types import EvaluationReport, GroundTruth


def evaluate_all(
    predictions: dict[str, ModelPrediction],
    ground_truth: GroundTruth,
    metadata: InferenceMetadata | None = None,
    conf_threshold: float = 0.25,
    iou_thresholds: Sequence[float] = DEFAULT_IOU_THRESHOLDS,
    class_aware: bool = True,
) -> EvaluationReport:
    """Run detection and counting evaluation and return one report.

    Counting uses the same confidence threshold as detection, so both halves of
    the report describe the same operating point.
    """
    detection = evaluate_detection(
        predictions,
        ground_truth,
        iou_thresholds=iou_thresholds,
        conf_threshold=conf_threshold,
        class_aware=class_aware,
    )
    counting = evaluate_counting(
        predicted_counts(predictions, conf_threshold),
        ground_truth.counts_by_image(),
    )
    return EvaluationReport(detection=detection, counting=counting, metadata=metadata)


def save_report(report: EvaluationReport, output_path: Path) -> None:
    """Write a report to ``output_path`` as indented JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
