"""End-to-end test tying the detection, counting and evaluation layers together.

Unit tests cover each layer in isolation; this exercises the contract that a
detector adapter's output flows through counting and evaluation unchanged, and
that a non-Ultralytics backend satisfies the same contract.
"""

import numpy as np

from aeronetra.counting.ops import count_vehicles
from aeronetra.detection.adapters import BaseDetector
from aeronetra.detection.types import BoundingBox, Detection, ModelPrediction
from aeronetra.evaluation.detection import evaluate_detection
from aeronetra.evaluation.types import GroundTruth, GroundTruthObject


class _StubDetector(BaseDetector):
    """A non-Ultralytics detector returning fixed boxes.

    It proves the pipeline depends only on the ``BaseDetector`` contract, not on
    any particular backend.
    """

    def load_model(self):
        self.model = object()

    def predict(self, image, conf_thresh=0.25, iou_thresh=0.45):
        return ModelPrediction(
            detections=[
                Detection(BoundingBox(0, 0, 10, 10), 0, "car", 0.9),
                Detection(BoundingBox(20, 20, 30, 30), 0, "car", 0.8),
            ],
            image_width=100,
            image_height=100,
        )


def test_stub_detector_flows_through_counting_and_evaluation():
    detector = _StubDetector("stub", "weights", {0: "car"})
    detector.load_model()
    prediction = detector.predict(np.zeros((100, 100, 3), dtype=np.uint8))

    total, per_class = count_vehicles(prediction.detections)
    assert (total, per_class) == (2, {"car": 2})

    ground_truth = GroundTruth()
    ground_truth.add_image(
        "img1",
        [
            GroundTruthObject(0, BoundingBox(0, 0, 10, 10)),
            GroundTruthObject(0, BoundingBox(20, 20, 30, 30)),
        ],
    )

    metrics = evaluate_detection({"img1": prediction}, ground_truth)

    assert metrics.precision == 1.0
    assert metrics.recall == 1.0
