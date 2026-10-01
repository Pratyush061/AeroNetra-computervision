"""Unit tests for the detector adapter factory and output normalization."""

from types import SimpleNamespace

import numpy as np
import pytest

from aeronetra.detection.adapters import UltralyticsAdapter, get_model_adapter


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
