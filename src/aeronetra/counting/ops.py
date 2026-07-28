"""Bounding-box coordinate conversions, clipping, filtering, NMS, and counting."""

from typing import List, Optional, Tuple

import cv2
import logging
import numpy as np

from aeronetra.detection.types import BoundingBox, Detection

logger = logging.getLogger(__name__)

def convert_xywh_to_xyxy(x: float, y: float, w: float, h: float) -> Tuple[float, float, float, float]:
    """Converts top-left xywh to xyxy."""
    return (x, y, x + w, y + h)

def convert_yolo_to_xyxy(xc: float, yc: float, nw: float, nh: float, img_w: int, img_h: int) -> Tuple[float, float, float, float]:
    """Converts normalized YOLO to absolute xyxy."""
    w = nw * img_w
    h = nh * img_h
    x_center = xc * img_w
    y_center = yc * img_h
    return (x_center - w / 2, y_center - h / 2, x_center + w / 2, y_center + h / 2)

def clip_box(box: BoundingBox, img_w: int, img_h: int) -> BoundingBox:
    """Clips a bounding box to image boundaries."""
    return BoundingBox(
        xmin=max(0.0, min(float(img_w), box.xmin)),
        ymin=max(0.0, min(float(img_h), box.ymin)),
        xmax=max(0.0, min(float(img_w), box.xmax)),
        ymax=max(0.0, min(float(img_h), box.ymax))
    )

def filter_by_area(detections: List[Detection], min_area: float, max_area: Optional[float] = None) -> List[Detection]:
    """Filters detections based on minimum and maximum area."""
    valid = []
    for d in detections:
        a = d.box.area
        if a >= min_area and (max_area is None or a <= max_area):
            valid.append(d)
    return valid

def filter_by_aspect_ratio(detections: List[Detection], min_ratio: float, max_ratio: float) -> List[Detection]:
    """Filters detections by aspect ratio (width/height)."""
    valid = []
    for d in detections:
        h = d.box.height
        if h > 0:
            ratio = d.box.width / h
            if min_ratio <= ratio <= max_ratio:
                valid.append(d)
    return valid

def filter_by_roi(detections: List[Detection], roi_xyxy: Tuple[float, float, float, float]) -> List[Detection]:
    """Filters detections whose centers fall within the Region of Interest (xmin, ymin, xmax, ymax)."""
    rx1, ry1, rx2, ry2 = roi_xyxy
    valid = []
    for d in detections:
        cx, cy = d.box.center
        if rx1 <= cx <= rx2 and ry1 <= cy <= ry2:
            valid.append(d)
    return valid

def apply_nms(detections: List[Detection], iou_threshold: float) -> List[Detection]:
    """
    Applies traditional Non-Maximum Suppression using OpenCV.
    Avoid double-applying if the model adapter already provides end-to-end filtered predictions.
    """
    if not detections:
        return []

    boxes = []
    scores = []

    for d in detections:
        # cv2.dnn.NMSBoxes expects [x, y, w, h] (top-left xywh)
        boxes.append([d.box.xmin, d.box.ymin, d.box.width, d.box.height])
        scores.append(float(d.confidence))

    indices = cv2.dnn.NMSBoxes(boxes, scores, 0.0, iou_threshold)

    if len(indices) == 0:
        return []

    # NMSBoxes returns a list/array of indices. In some OpenCV versions it's flat, in some nested.
    indices = np.array(indices).flatten()
    return [detections[i] for i in indices]

def count_vehicles(detections: List[Detection]) -> Tuple[int, dict]:
    """Returns total count and per-class count of detections."""
    total = len(detections)
    class_counts = {}
    for d in detections:
        class_counts[d.class_name] = class_counts.get(d.class_name, 0) + 1
    return total, class_counts
