# Limitations

Known limitations and constraints of the AeroNetra project in its current phase.

---

## Phase Scope

- **Currently Phase 1 only** — static image vehicle detection and counting. Video tracking, unique vehicle counting across frames, geospatial analytics, and edge deployment are not implemented.

---

## Detection Pipeline Limitations

| Limitation | Impact | Details |
|------------|--------|---------|
| **Max detections ceiling** | Undercounting in dense scenes | Ultralytics models have a hardcoded `max_det=300` limit. In dense VisDrone scenes with hundreds of vehicles, this cap artificially limits the count. Configured in `configs/inference/inference.yaml`. |
| **Single-image inference only** | No batch processing | `adapter.predict()` accepts one image at a time. Batch inference is not supported by the adapter interface. |
| **NMS behavior differs by architecture** | Inconsistent cross-model comparison | YOLO models require post-processing NMS. RT-DETR is end-to-end and should NOT have NMS applied. Applying NMS to RT-DETR can suppress valid dense detections. |
| **No multi-class filtering in adapter** | Manual post-processing needed | The adapter returns all detected classes. Use `ModelPrediction.filter_by_class()` to keep only vehicle classes after prediction. |
| **Confidence calibration varies** | Thresholds not comparable across models | A 0.25 confidence in YOLOv8 represents different certainty than 0.25 in RT-DETR. Per-model threshold tuning is recommended. |

---

## Dataset Limitations

| Limitation | Impact |
|------------|--------|
| **Tiny objects in aerial imagery** | VisDrone vehicles can be only a few pixels wide, making detection extremely challenging. Small object detection is a known hard problem. |
| **Domain shift** | Models pretrained on ground-level datasets (COCO, UA-DETRAC) perform poorly on aerial imagery without fine-tuning. |
| **Label quality** | Raw datasets may contain out-of-bounds boxes, zero-area annotations, ignored regions, and class ambiguity. Always run `scripts/validate_dataset.py` before training. |
| **UAVDT not implemented** | `src/aeronetra/datasets/uavdt.py` is a stub that raises `NotImplementedError`. Do not rely on it. |

---

## Module Gaps

| Module | Status |
|--------|--------|
| `src/aeronetra/evaluation/` | Empty (`.gitkeep` only) — no evaluation metrics implemented |
| `src/aeronetra/utils/` | Empty (`.gitkeep` only) — no utility functions implemented |
| `src/aeronetra/datasets/uavdt.py` | Stub — raises `NotImplementedError` |
| `configs/experiments/` | Empty — no experiment configs defined |
| `configs/models/` | Empty — no model-specific configs defined |

---

## Testing Gaps

- `src/aeronetra/detection/types.py` — dataclass tests missing
- `src/aeronetra/visualization/plots.py` — no tests
- `src/aeronetra/config.py` — no tests
- `scripts/download_dataset.py` and `scripts/validate_dataset.py` — no tests

---

## Resource Requirements

- **GPU:** Recommended for inference notebooks (03–08). Required for training (notebook 07).
- **Storage:** VisDrone full dataset is several GB. Ensure sufficient disk space.
- **Kaggle credentials:** Required only for `scripts/download_dataset.py`.
