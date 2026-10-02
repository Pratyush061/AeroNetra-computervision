"""Unit tests for IoU and detection-to-ground-truth matching."""

from aeronetra.detection.types import BoundingBox, Detection
from aeronetra.evaluation.matching import filter_ignored_detections, iou, match_image
from aeronetra.evaluation.types import GroundTruthObject


def test_iou_identical_and_disjoint():
    box = BoundingBox(0, 0, 10, 10)
    assert iou(box, box) == 1.0
    assert iou(box, BoundingBox(20, 20, 30, 30)) == 0.0


def test_iou_half_overlap():
    a = BoundingBox(0, 0, 10, 10)
    b = BoundingBox(5, 0, 15, 10)
    # intersection 5*10=50, union 100+100-50=150
    assert iou(a, b) == 50 / 150


def test_match_image_is_greedy_by_confidence():
    ground_truth = [GroundTruthObject(0, BoundingBox(0, 0, 10, 10))]
    high = Detection(BoundingBox(0, 0, 10, 10), 0, "car", 0.9)
    low = Detection(BoundingBox(0, 0, 10, 10), 0, "car", 0.5)

    outcome = match_image([low, high], ground_truth, 0.5)

    # The highest-confidence detection claims the single ground truth.
    assert outcome.matched == [(1, 0)]
    assert outcome.unmatched_detections == [0]
    assert outcome.unmatched_ground_truths == []


def test_match_image_respects_class_by_default():
    ground_truth = [GroundTruthObject(1, BoundingBox(0, 0, 10, 10))]
    wrong_class = Detection(BoundingBox(0, 0, 10, 10), 0, "car", 0.9)

    assert match_image([wrong_class], ground_truth, 0.5).matched == []
    assert match_image([wrong_class], ground_truth, 0.5, class_aware=False).matched == [
        (0, 0)
    ]


def test_match_image_threshold_boundary():
    ground_truth = [GroundTruthObject(0, BoundingBox(0, 0, 10, 10))]
    det = Detection(BoundingBox(0, 0, 5, 10), 0, "car", 0.9)  # IoU == 0.5

    assert match_image([det], ground_truth, 0.5).matched == [(0, 0)]
    assert match_image([det], ground_truth, 0.6).matched == []


def test_filter_ignored_detections_drops_detections_centred_in_a_region():
    region = BoundingBox(100, 100, 300, 300)
    inside = Detection(BoundingBox(150, 150, 170, 170), 0, "car", 0.9)
    outside = Detection(BoundingBox(400, 400, 420, 420), 0, "car", 0.9)

    assert filter_ignored_detections([inside, outside], [region]) == [outside]


def test_filter_ignored_detections_is_a_noop_without_regions():
    det = Detection(BoundingBox(0, 0, 10, 10), 0, "car", 0.9)

    assert filter_ignored_detections([det], []) == [det]
