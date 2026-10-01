"""Unit tests for the core detection data structures."""

import pytest

from aeronetra.detection.types import (
    BoundingBox,
    CountSummary,
    Detection,
    InferenceMetadata,
    ModelPrediction,
)


def test_bounding_box_derived_properties():
    box = BoundingBox(10.0, 20.0, 50.0, 80.0)
    assert box.xyxy == (10.0, 20.0, 50.0, 80.0)
    assert (box.width, box.height) == (40.0, 60.0)
    assert (box.area, box.center) == (2400.0, (30.0, 50.0))


@pytest.mark.parametrize(
    ("coords", "message"),
    [
        ((60.0, 20.0, 50.0, 80.0), "xmin .* > xmax"),
        ((10.0, 90.0, 50.0, 20.0), "ymin .* > ymax"),
    ],
)
def test_bounding_box_rejects_inverted_coords(coords, message):
    with pytest.raises(ValueError, match=message):
        BoundingBox(*coords)


def test_detection_and_count_summary():
    det = Detection(BoundingBox(0, 0, 20, 20), 0, "car", 0.88, "YOLOv8", "img_01")
    assert (det.class_name, det.confidence) == ("car", 0.88)

    summary = CountSummary("img_01", 1, {"car": 1}, "YOLOv8")
    assert (summary.total_vehicles, summary.class_counts) == (1, {"car": 1})


def test_model_prediction_filters_are_non_mutating():
    box = BoundingBox(10.0, 10.0, 50.0, 50.0)
    dets = [
        Detection(box, 0, "car", 0.9),
        Detection(box, 0, "car", 0.5),
        Detection(box, 1, "truck", 0.7),
    ]
    pred = ModelPrediction(dets, 640, 640, 12.5)

    confident = pred.filter_by_confidence(0.6)
    assert [d.confidence for d in confident.detections] == [0.9, 0.7]
    assert len(pred.detections) == 3  # original prediction is left untouched

    trucks = pred.filter_by_class([1])
    assert [d.class_name for d in trucks.detections] == ["truck"]


def test_inference_metadata_fields_and_defaults():
    meta = InferenceMetadata(
        model_name="YOLOv8n",
        package_version="0.1.0",
        weights_path="outputs/models/yolov8n_visdrone_best.pt",
        dataset_version="VisDrone2019-DET-val",
        image_size=(640, 640),
        confidence_threshold=0.25,
        iou_threshold=0.45,
        seed=42,
        device="cpu",
    )
    assert meta.model_name == "YOLOv8n"
    assert (meta.confidence_threshold, meta.iou_threshold) == (0.25, 0.45)
    assert meta.timing_ms == 0.0
