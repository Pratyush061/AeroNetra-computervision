import math

import numpy as np
import pytest

from aeronetra.detection.adapters import UltralyticsAdapter, get_model_adapter


class _TensorLike:
    """Minimal stand-in for a torch tensor exposing the `.cpu().numpy()` API
    the adapter relies on, so this test needs no deep-learning dependency."""

    def __init__(self, array):
        self._array = np.asarray(array)

    def cpu(self):
        return self

    def numpy(self):
        return self._array


class MockResultBox:
    def __init__(self):
        self.xyxy = _TensorLike([[10.0, 10.0, 50.0, 50.0]])
        self.conf = _TensorLike([0.9])
        self.cls = _TensorLike([2])


class MockResult:
    def __init__(self):
        self.boxes = MockResultBox()


class MockYOLOModel:
    def __init__(self):
        self.device = "cpu"

    def to(self, device):
        pass

    def predict(self, source, conf, iou, device, verbose):
        return [MockResult()]


def test_adapter_normalization(monkeypatch):
    def mock_load(self):
        self.model = MockYOLOModel()

    monkeypatch.setattr(UltralyticsAdapter, "load_model", mock_load)

    class_names = {0: "person", 2: "car"}
    adapter = get_model_adapter("YOLOv8", "yolov8n.pt", class_names)
    adapter.load_model()

    dummy_image = np.zeros((100, 100, 3), dtype=np.uint8)
    prediction = adapter.predict(dummy_image)

    assert len(prediction.detections) == 1
    det = prediction.detections[0]
    assert det.class_name == "car"
    assert det.class_id == 2
    assert math.isclose(det.confidence, 0.9, rel_tol=1e-5)
    assert det.box.xmin == 10.0


def test_adapter_unsupported_model():
    with pytest.raises(ValueError, match="No adapter available for model"):
        get_model_adapter("FasterRCNN", "weights.pt", {0: "vehicle"})


def test_adapter_rtdetr_pattern():
    adapter = get_model_adapter("RT-DETR", "rtdetr-l.pt", {0: "vehicle"})
    assert isinstance(adapter, UltralyticsAdapter)
    assert adapter.model_type == "RT-DETR"


def test_adapter_predict_without_load():
    adapter = get_model_adapter("YOLOv8", "yolov8n.pt", {0: "vehicle"})
    dummy_image = np.zeros((10, 10, 3), dtype=np.uint8)
    with pytest.raises(RuntimeError, match="Model is not loaded"):
        adapter.predict(dummy_image)
