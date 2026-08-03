import numpy as np

from aeronetra.detection.types import BoundingBox, Detection
from aeronetra.counting.ops import (
    convert_xywh_to_xyxy,
    convert_yolo_to_xyxy,
    clip_box,
    filter_by_area,
    filter_by_roi,
    apply_nms,
)
from aeronetra.counting.drawing import draw_detections, draw_roi


def test_convert_xywh_to_xyxy():
    assert convert_xywh_to_xyxy(10, 20, 30, 40) == (10, 20, 40, 60)


def test_convert_yolo_to_xyxy():
    # xc=0.5, yc=0.5, w=0.2, h=0.2, img=1000x1000
    # abs center: 500, 500, abs w=200, abs h=200
    # -> 400, 400, 600, 600
    assert convert_yolo_to_xyxy(0.5, 0.5, 0.2, 0.2, 1000, 1000) == (400, 400, 600, 600)


def test_clip_box():
    box = BoundingBox(-10, 50, 1100, 950)
    clipped = clip_box(box, 1000, 1000)
    assert clipped.xmin == 0
    assert clipped.xmax == 1000
    assert clipped.ymin == 50
    assert clipped.ymax == 950


def test_filtering():
    b1 = BoundingBox(0, 0, 10, 10)  # Area 100, Center 5,5
    b2 = BoundingBox(10, 10, 50, 50)  # Area 1600, Center 30,30

    d1 = Detection(b1, 0, "car", 0.9)
    d2 = Detection(b2, 1, "truck", 0.8)

    # Area filter
    res = filter_by_area([d1, d2], 200)
    assert len(res) == 1
    assert res[0].class_name == "truck"

    # ROI filter
    res = filter_by_roi([d1, d2], (20, 20, 100, 100))
    assert len(res) == 1
    assert res[0].class_name == "truck"


def test_apply_nms():
    # Two overlapping boxes
    b1 = BoundingBox(10, 10, 50, 50)
    b2 = BoundingBox(12, 12, 48, 48)
    d1 = Detection(b1, 0, "car", 0.9)
    d2 = Detection(b2, 0, "car", 0.8)

    res = apply_nms([d1, d2], 0.5)
    assert len(res) == 1
    assert res[0].confidence == 0.9


def test_drawing():
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    d1 = Detection(BoundingBox(10, 10, 50, 50), 0, "car", 0.9)

    out = draw_detections(img, [d1])
    assert out.shape == (100, 100, 3)
    # Check if anything was drawn (image should not be all zeros)
    assert np.any(out > 0)

    out_roi = draw_roi(img, (20, 20, 80, 80))
    assert np.any(out_roi > 0)


def test_counting_logic():
    from aeronetra.counting.ops import count_vehicles

    b1 = BoundingBox(10, 10, 50, 50)
    d1 = Detection(b1, 0, "car", 0.9)
    d2 = Detection(b1, 0, "car", 0.8)
    d3 = Detection(b1, 1, "truck", 0.7)

    total, c_counts = count_vehicles([d1, d2, d3])
    assert total == 3
    assert c_counts["car"] == 2
    assert c_counts["truck"] == 1


def test_filtering_logic():
    from aeronetra.detection.types import ModelPrediction

    b1 = BoundingBox(10, 10, 50, 50)
    d1 = Detection(b1, 0, "car", 0.9)
    d2 = Detection(b1, 0, "car", 0.5)
    d3 = Detection(b1, 1, "truck", 0.7)

    pred = ModelPrediction(detections=[d1, d2, d3])

    filtered = pred.filter_by_confidence(0.6)
    assert len(filtered.detections) == 2
    assert d2 not in filtered.detections

    filtered = filtered.filter_by_class([0])
    assert len(filtered.detections) == 1
    assert filtered.detections[0].class_name == "car"


def test_export_utilities(tmp_path):
    from aeronetra.counting.drawing import export_to_json, export_to_csv
    import json
    import csv

    b1 = BoundingBox(10, 10, 50, 50)
    d1 = Detection(b1, 0, "car", 0.9)

    json_path = tmp_path / "test.json"
    export_to_json([d1], json_path)

    with open(json_path, "r") as f:
        data = json.load(f)
        assert len(data) == 1
        assert data[0]["class_name"] == "car"

    csv_path = tmp_path / "test.csv"
    export_to_csv([d1], csv_path)

    with open(csv_path, "r") as f:
        reader = csv.reader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[1][1] == "car"
