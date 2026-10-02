"""Unit tests for the combined evaluation report and its JSON export."""

import json

from aeronetra.detection.types import BoundingBox, Detection, ModelPrediction
from aeronetra.evaluation.report import evaluate_all, save_report
from aeronetra.evaluation.types import GroundTruth, GroundTruthObject


def _inputs():
    ground_truth = GroundTruth()
    ground_truth.add_image("a", [GroundTruthObject(0, BoundingBox(0, 0, 10, 10))])
    predictions = {
        "a": ModelPrediction([Detection(BoundingBox(0, 0, 10, 10), 0, "car", 0.9)])
    }
    return predictions, ground_truth


def test_evaluate_all_combines_detection_and_counting():
    predictions, ground_truth = _inputs()

    report = evaluate_all(predictions, ground_truth)

    assert report.detection.map50 == 1.0
    assert report.counting.mae == 0.0
    assert report.counting.total_actual == 1
    assert report.metadata is None


def test_save_report_writes_json(tmp_path):
    predictions, ground_truth = _inputs()
    report = evaluate_all(predictions, ground_truth)

    output_path = tmp_path / "nested" / "report.json"
    save_report(report, output_path)

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["detection"]["map50"] == 1.0
    assert data["counting"]["total_actual"] == 1
    # Integer class-id keys become strings once serialised to JSON.
    assert "0" in data["detection"]["per_class"]
