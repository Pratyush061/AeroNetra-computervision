"""IoU computation and greedy detection-to-ground-truth matching."""

from collections.abc import Sequence

from aeronetra.detection.types import BoundingBox, Detection
from aeronetra.evaluation.types import GroundTruthObject, MatchOutcome


def iou(a: BoundingBox, b: BoundingBox) -> float:
    """Return the intersection-over-union of two boxes (0.0 when disjoint)."""
    inter_w = min(a.xmax, b.xmax) - max(a.xmin, b.xmin)
    inter_h = min(a.ymax, b.ymax) - max(a.ymin, b.ymin)
    if inter_w <= 0.0 or inter_h <= 0.0:
        return 0.0
    intersection = inter_w * inter_h
    union = a.area + b.area - intersection
    return intersection / union if union > 0.0 else 0.0


def filter_ignored_detections(
    detections: list[Detection], ignore_boxes: Sequence[BoundingBox]
) -> list[Detection]:
    """Drop detections that fall inside an ignored region.

    A detection whose centre lies in an ignored region is excluded from
    evaluation entirely — neither a true nor a false positive — following the
    VisDrone convention that detections in ignored regions are not scored.
    Centre containment is used rather than IoU because aerial ignore regions are
    large: a small vehicle box inside one has a low IoU with it, so an IoU test
    would miss it. Complexity is O(D * R).

    Args:
        detections: Detections for a single image.
        ignore_boxes: Ignored-region boxes for the same image.

    Returns:
        The detections that are not inside any ignored region.
    """
    if not ignore_boxes:
        return detections
    kept: list[Detection] = []
    for detection in detections:
        cx, cy = detection.box.center
        if any(
            region.xmin <= cx <= region.xmax and region.ymin <= cy <= region.ymax
            for region in ignore_boxes
        ):
            continue
        kept.append(detection)
    return kept


def match_image(
    detections: list[Detection],
    ground_truth: list[GroundTruthObject],
    iou_threshold: float,
    class_aware: bool = True,
) -> MatchOutcome:
    """Greedily match detections to ground truths within a single image.

    Detections are considered highest-confidence first; each is assigned to the
    unmatched ground truth of the same class (when ``class_aware``) with the
    greatest IoU that reaches ``iou_threshold``. This mirrors the VOC/COCO rule
    used to build precision/recall curves. Complexity is O(D * G) per image.

    Args:
        detections: Predicted detections for the image.
        ground_truth: Annotated objects for the image.
        iou_threshold: Minimum IoU for a match.
        class_aware: Require matched boxes to share a class id.

    Returns:
        A :class:`MatchOutcome` with matched index pairs and the indices of any
        unmatched detections and ground truths.
    """
    order = sorted(
        range(len(detections)),
        key=lambda i: detections[i].confidence,
        reverse=True,
    )
    used = [False] * len(ground_truth)
    matched: list[tuple[int, int]] = []
    unmatched_detections: list[int] = []

    for det_index in order:
        detection = detections[det_index]
        best_iou = -1.0
        best_index = -1
        for gt_index, gt in enumerate(ground_truth):
            if used[gt_index] or (class_aware and gt.class_id != detection.class_id):
                continue
            value = iou(detection.box, gt.box)
            if value >= iou_threshold and value > best_iou:
                best_iou = value
                best_index = gt_index
        if best_index >= 0:
            used[best_index] = True
            matched.append((det_index, best_index))
        else:
            unmatched_detections.append(det_index)

    unmatched_ground_truths = [i for i, was_used in enumerate(used) if not was_used]
    return MatchOutcome(matched, unmatched_detections, unmatched_ground_truths)
