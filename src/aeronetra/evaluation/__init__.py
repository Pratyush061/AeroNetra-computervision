"""Evaluation metrics for detection and image-level counting.

This package completes the Phase 1 model-comparison workflow: it turns
standardised :class:`~aeronetra.detection.types.ModelPrediction` objects and a
:class:`~aeronetra.evaluation.types.GroundTruth` set into precision/recall,
mAP@50, mAP@50-95 and count-error metrics, with JSON export for experiment
records.
"""

from aeronetra.evaluation.counting import evaluate_counting, predicted_counts
from aeronetra.evaluation.detection import (
    DEFAULT_AP_CONFIDENCE,
    DEFAULT_IOU_THRESHOLDS,
    OPERATING_IOU,
    evaluate_detection,
)
from aeronetra.evaluation.groundtruth import (
    image_sizes_from_dir,
    load_visdrone_ground_truth,
    load_yolo_ground_truth,
)
from aeronetra.evaluation.matching import iou, match_image
from aeronetra.evaluation.report import evaluate_all, save_report
from aeronetra.evaluation.types import (
    ClassMetrics,
    CountMetrics,
    DetectionMetrics,
    EvaluationReport,
    GroundTruth,
    GroundTruthImage,
    GroundTruthObject,
    ImageCountError,
    MatchOutcome,
)

__all__ = [
    "DEFAULT_AP_CONFIDENCE",
    "DEFAULT_IOU_THRESHOLDS",
    "OPERATING_IOU",
    "ClassMetrics",
    "CountMetrics",
    "DetectionMetrics",
    "EvaluationReport",
    "GroundTruth",
    "GroundTruthImage",
    "GroundTruthObject",
    "ImageCountError",
    "MatchOutcome",
    "evaluate_all",
    "evaluate_counting",
    "evaluate_detection",
    "image_sizes_from_dir",
    "iou",
    "load_visdrone_ground_truth",
    "load_yolo_ground_truth",
    "match_image",
    "predicted_counts",
    "save_report",
]
