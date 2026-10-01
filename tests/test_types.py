import pytest

from aeronetra.detection.types import (
    BoundingBox,
    CountSummary,
    Detection,
    InferenceMetadata,
    ModelPrediction,
)


def test_bounding_box_valid():
    box = BoundingBox(10.0, 20.0, 50.0, 80.0)
    assert box.xyxy == (10.0, 20.0, 50.0, 80.0)
    assert box.width == 40.0
    assert box.height == 60.0
    assert box.area == 2400.0
    assert box.center == (30.0, 50.0)


def test_bounding_box_invalid_coords():
    with pytest.raises(ValueError, match="xmin .* > xmax"):
        BoundingBox(60.0, 20.0, 50.0, 80.0)

    with pytest.raises(ValueError, match="ymin .* > ymax"):
        BoundingBox(10.0, 90.0, 50.0, 20.0)


def test_detection_and_summary():
    box = BoundingBox(0.0, 0.0, 20.0, 20.0)
    det = Detection(
        box=box,
        class_id=0,
        class_name="car",
        confidence=0.88,
        source_model="YOLOv8",
        image_id="img_01",
    )
    assert det.class_name == "car"
    assert det.confidence == 0.88

    summary = CountSummary(
        image_id="img_01",
        total_vehicles=1,
        class_counts={"car": 1},
    )
    assert summary.total_vehicles == 1
    assert summary.class_counts["car"] == 1


def test_model_prediction_filtering():
    b1 = BoundingBox(10.0, 10.0, 50.0, 50.0)
    d1 = Detection(b1, 0, "car", 0.9)
    d2 = Detection(b1, 0, "car", 0.5)
    d3 = Detection(b1, 1, "truck", 0.7)

    pred = ModelPrediction(
        detections=[d1, d2, d3],
        image_width=640,
        image_height=640,
        inference_time_ms=12.5,
    )

    filtered_conf = pred.filter_by_confidence(0.6)
    assert len(filtered_conf.detections) == 2
    assert d2 not in filtered_conf.detections
    assert len(pred.detections) == 3

    filtered_cls = pred.filter_by_class([1])
    assert len(filtered_cls.detections) == 1
    assert filtered_cls.detections[0].class_name == "truck"


def test_inference_metadata():
    meta = InferenceMetadata(
        model_name="YOLOv8n",
        weights_path="outputs/models/yolov8n_visdrone_best.pt",
        dataset_name="VisDrone",
        dataset_split="val",
        image_size=(640, 640),
        confidence_threshold=0.25,
        iou_threshold=0.45,
        device="cpu",
    )
    assert meta.model_name == "YOLOv8n"
    assert meta.confidence_threshold == 0.25
    assert meta.iou_threshold == 0.45
