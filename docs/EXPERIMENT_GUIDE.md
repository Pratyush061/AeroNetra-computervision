# Experiment Guide

Guidelines for conducting, recording, and comparing experiments in AeroNetra.

---

## Recording Experiment Metadata

Every inference run **must** use the `InferenceMetadata` dataclass from `src/aeronetra/detection/types.py`. All fields are mandatory.

```python
from aeronetra.detection.types import InferenceMetadata

metadata = InferenceMetadata(
    model_name="YOLOv8n",                    # Architecture name
    package_version="8.0.0",                 # ultralytics version
    weights_path="outputs/models/yolov8n.pt",# Path to weights file
    dataset_version="VisDrone2019-DET-val",  # Dataset split used
    image_size=(640, 640),                   # Input resolution
    confidence_threshold=0.25,               # From inference.yaml
    iou_threshold=0.45,                      # From inference.yaml
    seed=42,                                 # Random seed for reproducibility
    device="cuda",                           # "cpu" or "cuda"
    timing_ms=15.3                           # Inference time in milliseconds
)
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `model_name` | str | Architecture identifier (e.g., "YOLOv8n", "RT-DETR-l") |
| `package_version` | str | Version of the inference library (e.g., ultralytics version) |
| `weights_path` | str | Path to the model weights file used |
| `dataset_version` | str | Dataset and split identifier |
| `image_size` | Tuple[int, int] | Input image resolution (width, height) |
| `confidence_threshold` | float | Confidence threshold applied |
| `iou_threshold` | float | IoU threshold for NMS |
| `seed` | int | Random seed used |
| `device` | str | Compute device ("cpu" or "cuda") |
| `timing_ms` | float | Total inference time in milliseconds |

---

## Configuration Source

Load inference parameters from `configs/inference/inference.yaml` (not from `config.py` defaults):

```yaml
image_size: [640, 640]
confidence_threshold: 0.25
iou_threshold: 0.45
max_detections: 300
device: "cpu"
```

> **Note:** `config.py` has `DEFAULT_CONFIDENCE = 0.5`, but `inference.yaml` uses `0.25`. YAML values are authoritative for experiments.

---

## Validation Split Management

- Always compare models on the **same validation split** — never compare results from different splits.
- Do not claim a model is "best" without measured evidence from that shared validation split.
- Record the exact split used in `dataset_version` (e.g., "VisDrone2019-DET-val", not just "VisDrone").

---

## Output Directory Structure

Experiment outputs go in the `outputs/` directory (gitignored):

```
outputs/
├── metrics/         ← Evaluation metrics (JSON, CSV)
├── models/          ← Trained/fine-tuned model weights
├── predictions/     ← Detection results (JSON, CSV exports)
└── visualizations/  ← Annotated images, plots
```

Use `export_to_json()` and `export_to_csv()` from `src/aeronetra/counting/drawing.py` for standardized export.

---

## Best Practices

1. **Deterministic seeds.** Set random seeds for reproducibility. Record the seed in `InferenceMetadata`.
2. **Never fabricate results.** Only record actually measured values. Clearly mark unexecuted experiments.
3. **Threshold tuning.** Tune confidence thresholds per model on a hold-out set before comparing final counts.
4. **Max detections awareness.** The `max_detections: 300` ceiling can cap counts in dense aerial scenes — note this when analyzing results. See [MODEL_COMPARISON.md](MODEL_COMPARISON.md) for details.
5. **NMS caution.** Do not apply NMS to RT-DETR outputs — it is end-to-end and handles suppression internally.
6. **Dataset validation.** Run `python scripts/validate_dataset.py` before training to catch label issues.
