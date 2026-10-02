"""Unit tests for the detector adapter factory and output normalization."""

from types import SimpleNamespace

import numpy as np
import pytest

from aeronetra.detection.adapters import (
    OnnxRuntimeAdapter,
    UltralyticsAdapter,
    get_model_adapter,
)


class _TensorLike:
    """Stand-in for a torch tensor exposing the `.cpu().numpy()` API the
    adapter relies on, so these tests need no deep-learning dependency."""

    def __init__(self, array):
        self._array = np.asarray(array)

    def cpu(self):
        return self

    def numpy(self):
        return self._array


def _mock_model():
    """Fake Ultralytics model that returns a single canned detection."""
    boxes = SimpleNamespace(
        xyxy=_TensorLike([[10.0, 10.0, 50.0, 50.0]]),
        conf=_TensorLike([0.9]),
        cls=_TensorLike([2]),
    )
    return SimpleNamespace(predict=lambda **_: [SimpleNamespace(boxes=boxes)])


def test_predict_normalizes_boxes(monkeypatch):
    def fake_load(self):
        self.model = _mock_model()

    monkeypatch.setattr(UltralyticsAdapter, "load_model", fake_load)
    adapter = get_model_adapter("YOLOv8", "yolov8n.pt", {0: "person", 2: "car"})
    adapter.load_model()

    prediction = adapter.predict(np.zeros((100, 100, 3), dtype=np.uint8))

    assert len(prediction.detections) == 1
    det = prediction.detections[0]
    assert (det.class_id, det.class_name) == (2, "car")
    assert det.confidence == pytest.approx(0.9)
    assert det.box.xyxy == (10.0, 10.0, 50.0, 50.0)


@pytest.mark.parametrize(
    "model_name", ["YOLOv8", "YOLO11", "YOLO26", "RT-DETR", "rtdetr"]
)
def test_supported_models_build_ultralytics_adapter(model_name):
    adapter = get_model_adapter(model_name, "weights.pt", {0: "vehicle"})
    assert isinstance(adapter, UltralyticsAdapter)
    assert adapter.model_type == model_name


def test_unsupported_model_raises():
    with pytest.raises(ValueError, match="No adapter available for model"):
        get_model_adapter("FasterRCNN", "weights.pt", {0: "vehicle"})


def test_predict_before_load_raises():
    adapter = get_model_adapter("YOLOv8", "yolov8n.pt", {0: "vehicle"})
    with pytest.raises(RuntimeError, match="Model not loaded"):
        adapter.predict(np.zeros((10, 10, 3), dtype=np.uint8))


class _FakeOnnxSession:
    """Stand-in for an ONNX Runtime session that returns a canned output."""

    def __init__(self, output):
        self._output = output

    def run(self, *_args, **_kwargs):
        return [self._output]


def _onnx_adapter(output, class_names):
    adapter = OnnxRuntimeAdapter(
        "yolov8n.onnx", "model.onnx", class_names, input_size=(640, 640)
    )
    adapter.session = _FakeOnnxSession(output)
    adapter.input_name = "images"
    return adapter


def test_factory_builds_onnx_adapter_for_onnx_names():
    adapter = get_model_adapter("yolov8n.onnx", "m.onnx", {0: "vehicle"})

    assert isinstance(adapter, OnnxRuntimeAdapter)


def test_onnx_predict_parses_raw_channel_first_layout():
    # (1, 4+nc, N) with nc=1: rows are cx, cy, w, h, score for two anchors.
    output = np.array(
        [
            [320.0, 100.0],
            [320.0, 100.0],
            [40.0, 20.0],
            [40.0, 20.0],
            [0.9, 0.1],  # second anchor is below the confidence threshold
        ]
    )[np.newaxis]
    adapter = _onnx_adapter(output, {0: "vehicle"})

    prediction = adapter.predict(np.zeros((640, 640, 3), dtype=np.uint8))

    assert len(prediction.detections) == 1
    det = prediction.detections[0]
    assert det.box.xyxy == (300.0, 300.0, 340.0, 340.0)
    assert det.confidence == pytest.approx(0.9)
    assert (det.class_id, det.class_name) == (0, "vehicle")


def test_onnx_predict_applies_nms_to_raw_layout():
    # Two identical, heavily overlapping same-class anchors collapse to one.
    output = np.array(
        [
            [150.0, 150.0],
            [150.0, 150.0],
            [100.0, 100.0],
            [100.0, 100.0],
            [0.9, 0.8],
        ]
    )[np.newaxis]
    adapter = _onnx_adapter(output, {0: "vehicle"})

    prediction = adapter.predict(np.zeros((640, 640, 3), dtype=np.uint8))

    assert len(prediction.detections) == 1
    assert prediction.detections[0].confidence == pytest.approx(0.9)


def test_onnx_predict_parses_end_to_end_layout_without_nms():
    # (1, N, 6): x1, y1, x2, y2, conf, class — already suppressed, so two
    # overlapping boxes are both kept.
    output = np.array(
        [
            [
                [100.0, 100.0, 200.0, 200.0, 0.9, 0.0],
                [105.0, 105.0, 205.0, 205.0, 0.8, 0.0],
            ]
        ]
    )
    adapter = _onnx_adapter(output, {0: "vehicle"})

    prediction = adapter.predict(np.zeros((640, 640, 3), dtype=np.uint8))

    assert len(prediction.detections) == 2


def test_onnx_predict_before_load_raises():
    adapter = get_model_adapter("onnx", "m.onnx", {0: "vehicle"})

    with pytest.raises(RuntimeError, match="Model not loaded"):
        adapter.predict(np.zeros((10, 10, 3), dtype=np.uint8))
