# Model Comparison

This document explains the nuances of comparing different object detection architectures (e.g., YOLO vs. RT-DETR) for aerial vehicle counting.

---

## Identical Thresholds Do Not Mean Identical Post-Processing

Using the same confidence and IoU thresholds across different models (e.g., from `configs/inference/inference.yaml`) does **not** make architectures directly comparable.

### 1. Confidence Calibration

- **YOLO models** (v8, 11, 26) have different internal confidence calibrations. A 0.25 confidence score in YOLOv8 represents a different certainty level than 0.25 in YOLO11.
- **RT-DETR** (transformer-based) outputs probabilities differently than anchor-based or anchor-free CNNs.
- **Recommendation:** Tune confidence thresholds **per model** on a hold-out validation set to match a target precision/recall trade-off before comparing final counts.

### 2. Non-Maximum Suppression (NMS)

- **YOLO models** require NMS as a post-processing step to remove duplicate overlapping boxes. The codebase uses `cv2.dnn.NMSBoxes` in `src/aeronetra/counting/ops.py`.
- **RT-DETR** is inherently end-to-end — the transformer decoder naturally suppresses duplicate predictions. **Do NOT apply additional NMS to RT-DETR outputs.** Doing so can accidentally suppress valid, dense detections.

### 3. Maximum Detections Ceiling

Models have a hardcoded limit on maximum detections per image. In `configs/inference/inference.yaml`:

```yaml
max_detections: 300
```

In dense aerial scenes (VisDrone) with hundreds of small vehicles, this ceiling can:
- Artificially cap the vehicle count
- Make a superior model look equivalent to a worse one (both hit the same ceiling)
- Cause underreporting in heavy traffic areas

**Always note the `max_detections` value** when analyzing results from dense scenes.

---

## Model Architecture Summary

| Architecture | NMS Required | Inference Speed | Small Object Performance | Notes |
|-------------|:------------:|:---------------:|:------------------------:|-------|
| YOLOv8 | ✅ Yes | Fast | Good | Well-established baseline |
| YOLO11 | ✅ Yes | Fast | Good | Newer YOLO variant |
| YOLOv26 | ✅ Yes | Fast | Good | Latest YOLO variant |
| RT-DETR | ❌ No (end-to-end) | Moderate | Variable | Transformer-based; no NMS needed |

All models are accessed through the same `UltralyticsAdapter` — the only difference is the weights file and the NMS behavior.

---

## Best Practices for Fair Comparison

1. **Same validation split.** Compare models on the **exact same images** — never compare results from different splits or random subsets.
2. **Per-model threshold tuning.** Tune confidence thresholds individually on a hold-out set before comparing final counts.
3. **Watch `max_det`.** In dense scenes, check if results are limited by the 300-detection ceiling.
4. **Record metadata.** Use `InferenceMetadata` from `src/aeronetra/detection/types.py` to track exact parameters for every run.
5. **Same input resolution.** Ensure all models use the same `image_size` (default: 640×640 from `inference.yaml`).
6. **Do not apply NMS to RT-DETR.** This is the most common error when comparing architectures.
7. **Statistical significance.** Single-image comparisons are anecdotal. Evaluate across the full validation set.
