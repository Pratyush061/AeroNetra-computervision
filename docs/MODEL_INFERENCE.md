# Model Inference Guide

This document describes how object detection inference is structured and executed in the AeroNetra project.

---

## The Model Adapter Interface

All object detectors interact through a common adapter interface defined in `src/aeronetra/detection/adapters.py`. This ensures consistent behavior across architectures.

### `BaseDetector` (Abstract Base Class)

| Method | Signature | Description |
|--------|-----------|-------------|
| `load_model()` | `() → None` | Loads weights into memory and moves model to target device. **Must be called before `predict()`.** |
| `predict()` | `(image: np.ndarray, conf_thresh: float, iou_thresh: float) → ModelPrediction` | Runs inference on a single image. Returns standardized `ModelPrediction`. |

### `UltralyticsAdapter`

The only currently implemented adapter. Supports all models from the `ultralytics` package:
- **YOLO:** YOLOv8, YOLO11, YOLOv26
- **RT-DETR:** RT-DETR-l, RT-DETR-x

### `get_model_adapter()` Factory Function

```python
get_model_adapter(
    model_name: str,          # "YOLOv8", "YOLO11", "YOLOv26", "RT-DETR"
    weights_path: str,        # Path to .pt weights file
    class_names: dict,        # {0: "vehicle"} or {0: "bicycle", 1: "car", ...}
    device: str = "cpu"       # "cpu" or "cuda"
) → BaseDetector
```

---

## Usage Flow

```python
from aeronetra.detection.adapters import get_model_adapter

# Step 1: Create adapter via factory
adapter = get_model_adapter(
    model_name="YOLOv8",
    weights_path="outputs/models/yolov8n.pt",
    class_names={0: "vehicle"},
    device="cuda"  # or "cpu"
)

# Step 2: Load model explicitly (REQUIRED before predict)
adapter.load_model()

# Step 3: Run inference — returns ModelPrediction
prediction = adapter.predict(image_array, conf_thresh=0.25, iou_thresh=0.45)

# Step 4: Use standardized outputs
for det in prediction.detections:
    print(det.box.xyxy, det.class_name, det.confidence)

# Optional: Filter results
prediction.filter_by_confidence(0.5)
prediction.filter_by_class([0, 1, 2])

# Step 5: Count and draw
from aeronetra.counting.ops import count_vehicles
from aeronetra.counting.drawing import draw_detections

total, by_class = count_vehicles(prediction.detections)
annotated = draw_detections(image_array.copy(), prediction.detections)
```

---

## Standardized Outputs

Regardless of model architecture, the adapter normalizes all outputs into these dataclasses from `src/aeronetra/detection/types.py`:

### `ModelPrediction`
| Field | Type | Description |
|-------|------|-------------|
| `detections` | `List[Detection]` | All detected objects |
| `image_width` | `int` | Input image width in pixels |
| `image_height` | `int` | Input image height in pixels |
| `inference_time_ms` | `float` | Inference time in milliseconds |

Methods: `filter_by_confidence(threshold)`, `filter_by_class(allowed_classes)`

### `Detection`
| Field | Type | Description |
|-------|------|-------------|
| `box` | `BoundingBox` | Bounding box in xyxy absolute pixel coordinates |
| `class_id` | `int` | Integer class ID |
| `class_name` | `str` | Human-readable class name |
| `confidence` | `float` | Confidence score (0.0–1.0) |
| `source_model` | `str` | Model identifier (default: "unknown") |
| `image_id` | `str` | Image identifier (default: "unknown") |

### `BoundingBox`
| Field | Type | Description |
|-------|------|-------------|
| `xmin`, `ymin`, `xmax`, `ymax` | `float` | Absolute pixel coordinates (xyxy format) |

Properties: `width`, `height`, `area`, `center`, `xyxy`

---

## Error Handling

| Scenario | Error | Solution |
|----------|-------|----------|
| `predict()` called before `load_model()` | `RuntimeError` | Always call `adapter.load_model()` first |
| Weights file not found | `FileNotFoundError` | Verify `weights_path` is correct |
| Invalid model name in factory | `ValueError` | Use supported names: "YOLOv8", "YOLO11", "YOLOv26", "RT-DETR" |

---

## Important Rules

- **Never instantiate models directly** — always use `get_model_adapter()`.
- **Never auto-download weights** — weights paths must be explicitly provided.
- **Single image only** — `predict()` takes one NumPy array; batch inference is not supported.
- **Device must be specified** — set `device="cuda"` for GPU or `device="cpu"` for CPU.
- **Load thresholds from YAML** — use `configs/inference/inference.yaml` values (conf=0.25, iou=0.45), not `config.py` defaults (conf=0.5).
- **Do not apply NMS to RT-DETR** — it is end-to-end and handles suppression internally.
