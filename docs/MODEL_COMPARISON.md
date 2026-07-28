# Model Comparison

This document explains the nuances of comparing different object detection architectures (e.g., YOLO vs. RT-DETR) for aerial vehicle counting.

## Identical Thresholds Do Not Mean Identical Post-Processing
Using the same confidence and IoU thresholds across different models (e.g., in `configs/inference/inference.yaml`) does **not** make architectures completely comparable.

### 1. Confidence Calibration
- **YOLO models** (v8, 11, 26) often have different internal confidence calibrations. A 0.25 confidence score in YOLOv8 might represent a different certainty level than a 0.25 in YOLO11.
- **RT-DETR** (a transformer-based model) outputs probabilities differently than anchor-based or anchor-free CNNs.

### 2. Non-Maximum Suppression (NMS)
- YOLO models typically require NMS as a post-processing step to remove duplicate overlapping boxes.
- RT-DETR models are inherently end-to-end and often do not require traditional NMS, as the transformer decoder naturally learns to suppress duplicate predictions. Applying OpenCV NMS on top of RT-DETR outputs might accidentally suppress valid, dense detections.

### 3. Maximum Detections
Models often have hardcoded limits on the maximum number of detections per image (e.g., `max_det=300`). In dense aerial scenes with hundreds of small vehicles, this limit can artificially cap the vehicle count, making a superior model look equivalent to a worse one simply because both hit the ceiling.

## Best Practices for Comparison
1. Compare models on the **same validation split** (not just a single sample image).
2. Tune confidence thresholds **per model** on a hold-out set to match a target precision/recall trade-off before comparing final counts.
3. Be aware of the `max_det` parameter when analyzing dense scenes like those in VisDrone.
