# Counting Methodology

This document explains the methodology and limitations for counting vehicles based on image-level object detection bounding boxes.

> **Current Phase:** Phase 1 implements image-level counting only. Unique vehicle counting across video frames (requiring tracking) is planned for Phase 3.

---

## Core Distinction

- **Image-level Count:** The number of bounding boxes (vehicles) detected in a single image. This is what `count_vehicles()` in `src/aeronetra/counting/ops.py` returns — a tuple of `(total_count, class_counts_dict)`.
- **Unique Vehicle Count:** Requires multi-object tracking (MOT) across a video sequence to prevent double-counting. Image-level counting is *not* unique vehicle tracking. **This is not implemented in Phase 1.**

---

## Counting Pipeline

The implemented counting flow uses functions from `src/aeronetra/counting/ops.py`:

```
Image → Model Adapter → ModelPrediction → [Optional Filtering] → count_vehicles()
                                               ↓
                                    filter_by_area()
                                    filter_by_aspect_ratio()
                                    filter_by_roi()
                                    apply_nms()  ← YOLO only, NOT RT-DETR
```

| Function | Module | Purpose |
|----------|--------|---------|
| `count_vehicles(detections)` | `ops.py` | Returns `(total_count, class_counts_dict)` |
| `filter_by_area(detections, min_area, max_area)` | `ops.py` | Remove too-small or too-large boxes |
| `filter_by_aspect_ratio(detections, min_ratio, max_ratio)` | `ops.py` | Remove extreme aspect ratios |
| `filter_by_roi(detections, roi)` | `ops.py` | Keep only detections inside a Region of Interest |
| `apply_nms(boxes, scores, iou_thresh)` | `ops.py` | NMS via `cv2.dnn.NMSBoxes` — **YOLO only** |

---

## Challenges with Bounding-Box Counting in Aerial Imagery

Counting vehicles by summing detected bounding boxes is imperfect. Be aware of the following issues:

1. **Missed Detections (False Negatives):** Models may fail to detect vehicles due to poor lighting, occlusion, or objects being too small.
2. **Duplicate Detections (False Positives):** Inadequate NMS or low thresholds can lead to the same vehicle being counted multiple times.
3. **Occlusion:** Vehicles partially hidden by trees, buildings, or other vehicles might be missed or detected with lower confidence.
4. **Tiny Vehicles:** In drone imagery, vehicles can appear very small (few pixels wide). Small object detection is a notoriously hard problem. VisDrone is especially affected.
5. **Class Confusion:** The model might mistake a van for a car or a truck for a bus, affecting per-class counts (though total count remains correct).
6. **Frame Edges:** Vehicles cut off by image edges might not be detected or might generate low-confidence partial detections.
7. **Dense Scenes:** In heavy traffic, overlapping boxes make traditional NMS struggle — it may suppress valid detections. The `max_detections: 300` ceiling in `configs/inference/inference.yaml` further limits counts.
8. **Domain Shift:** Models trained on ground-level imagery (like COCO or UA-DETRAC) often perform poorly on aerial imagery without fine-tuning.

---

## Mitigation Strategies

| Strategy | Implementation | Notes |
|----------|---------------|-------|
| **ROI Filtering** | `filter_by_roi(detections, roi)` | Count vehicles only in specific areas |
| **Threshold Tuning** | `conf_thresh` and `iou_thresh` parameters | Tune per model on validation data, not blindly |
| **Area Filtering** | `filter_by_area(detections, min_area, max_area)` | Remove impossibly small or large boxes |
| **Aspect Ratio Filtering** | `filter_by_aspect_ratio(detections, min_ratio, max_ratio)` | Remove non-vehicle-shaped detections |
| **NMS (YOLO only)** | `apply_nms(boxes, scores, iou_thresh)` | Suppress duplicate overlapping boxes |
| **Class Filtering** | `ModelPrediction.filter_by_class(allowed_classes)` | Keep only vehicle classes |

> **Warning:** Do not apply NMS to RT-DETR outputs — it is end-to-end and handles duplicate suppression internally.
