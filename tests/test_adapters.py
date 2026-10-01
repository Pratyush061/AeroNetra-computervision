import numpy as np

from aeronetra.detection.adapters import get_model_adapter


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
        self.device = device

    def predict(self, source, conf, iou, device, verbose):
        return [MockResult()]

def test_adapter_normalization(monkeypatch):
    from aeronetra.detection.adapters import UltralyticsAdapter

    # Mock the loading logic
    def mock_load(self):
        self.model = MockYOLOModel()

    monkeypatch.setattr(UltralyticsAdapter, "load_model", mock_load)

    adapter = get_model_adapter("YOLO11", "dummy.pt", {2: "car"})
    adapter.load_model()

    dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
    pred = adapter.predict(dummy_img, conf_thresh=0.25)

    assert len(pred.detections) == 1
    det = pred.detections[0]
    assert det.class_name == "car"
    assert det.class_id == 2
    import math
    assert math.isclose(det.confidence, 0.9, rel_tol=1e-5)
    assert det.box.xmin == 10.0
