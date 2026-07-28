# Instructions for Coding Agents

This repository is **AeroNetra**, a computer-vision research project for UAV/drone-based vehicle detection and counting. This file is the authoritative reference for AI coding agents. Every instruction below is grounded in the actual codebase — follow them exactly.

---

## 1. Core Directives

- **Research software only.** This is NOT a website, mobile app, dashboard, API product, or SaaS. Never add frontend frameworks, web servers, or UI code unless explicitly requested.
- **Inspect before editing.** Always read existing files before modifying them. Preserve useful code and avoid unnecessary overwrites or refactors.
- **Small, reviewable changes.** Prefer smaller, iterative modifications over large rewrites.
- **Current phase is Phase 1** — static image vehicle detection and counting. Do NOT implement video tracking, geospatial analytics, or edge deployment unless explicitly asked.

---

## 2. Project Structure (Exact)

```
├── AGENTS.md                  ← THIS FILE — agent instructions
├── README.md                  ← Project overview and quick start
├── DEVELOPER_GUIDE.md         ← Human developer onboarding
├── pyproject.toml             ← Package metadata and build config
├── requirements.txt           ← Runtime dependencies
├── requirements-dev.txt       ← Development dependencies (pytest, ruff)
├── .env.example               ← Template for environment variables
│
├── src/aeronetra/             ← ALL reusable Python library code
│   ├── __init__.py            ← Package init (version string only)
│   ├── config.py              ← Paths (ROOT_DIR, DATA_DIR) and defaults
│   ├── detection/
│   │   ├── adapters.py        ← BaseDetector ABC, UltralyticsAdapter, get_model_adapter()
│   │   └── types.py           ← BoundingBox, Detection, ModelPrediction, CountSummary, InferenceMetadata
│   ├── counting/
│   │   ├── ops.py             ← Coordinate conversions, filtering, NMS, count_vehicles()
│   │   └── drawing.py         ← draw_detections(), draw_roi(), export_to_json/csv()
│   ├── datasets/
│   │   ├── visdrone.py        ← VisDrone parser, converter, class mapping (IMPLEMENTED)
│   │   └── uavdt.py           ← STUB — raises NotImplementedError (NOT implemented)
│   ├── visualization/
│   │   └── plots.py           ← plot_class_distribution(), plot_size_distribution()
│   ├── evaluation/            ← STUB — only .gitkeep (NOT implemented)
│   └── utils/                 ← STUB — only .gitkeep (NOT implemented)
│
├── configs/
│   ├── datasets/              ← YAML dataset configs (visdrone_merged.yaml, etc.)
│   ├── inference/
│   │   └── inference.yaml     ← Shared inference hyperparameters
│   ├── experiments/           ← Empty — experiment configs go here
│   └── models/                ← Empty — model configs go here
│
├── notebooks/                 ← Jupyter notebooks (numbered 00–08 progression)
│   ├── 00_environment_check.ipynb
│   ├── 01_dataset_exploration.ipynb
│   ├── 02_opencv_vehicle_counting.ipynb
│   ├── 03_yolo26_inference.ipynb
│   ├── 04_yolo11_inference.ipynb
│   ├── 05_yolov8_inference.ipynb
│   ├── 06_rtdetr_inference.ipynb
│   ├── 07_model_training.ipynb
│   └── 08_model_evaluation.ipynb
│
├── scripts/
│   ├── download_dataset.py    ← Kaggle dataset downloader (requires --download flag)
│   └── validate_dataset.py    ← YOLO format dataset validator
│
├── tests/
│   ├── test_adapters.py       ← Adapter normalization tests (mock model)
│   ├── test_counting.py       ← Coordinate, filtering, NMS, drawing, export tests
│   ├── test_visdrone.py       ← VisDrone parsing, conversion, class mapping tests
│   ├── fixtures/              ← Test data (sample labels, images)
│   ├── unit/                  ← Additional unit tests
│   └── integration/           ← Integration tests
│
├── data/                      ← GITIGNORED — raw/interim/processed datasets
├── outputs/                   ← GITIGNORED — metrics, models, predictions, visualizations
└── docs/                      ← Detailed documentation files
```

### Stubs That Do NOT Exist Yet

These modules are placeholders. **Never fabricate implementations or claim they work:**

| Path | Status | Notes |
|------|--------|-------|
| `src/aeronetra/datasets/uavdt.py` | Stub | Raises `NotImplementedError` |
| `src/aeronetra/evaluation/` | Empty | Only contains `.gitkeep` |
| `src/aeronetra/utils/` | Empty | Only contains `.gitkeep` |
| `configs/experiments/` | Empty | No experiment configs yet |
| `configs/models/` | Empty | No model configs yet |

---

## 3. Model Adapter Contract

All object detection models **MUST** use the adapter interface. Never instantiate models directly.

### Required Flow

```python
from aeronetra.detection.adapters import get_model_adapter

# Step 1: Create adapter via factory (NEVER instantiate YOLO/RTDETR directly)
adapter = get_model_adapter(
    model_name="YOLOv8",          # or "YOLO11", "YOLOv26", "RT-DETR"
    weights_path="path/to/weights.pt",
    class_names={0: "vehicle"},    # dict mapping class_id → name
    device="cpu"                   # or "cuda"
)

# Step 2: Explicitly load model (MUST call before predict)
adapter.load_model()

# Step 3: Run inference — returns ModelPrediction
prediction = adapter.predict(image_array, conf_thresh=0.25, iou_thresh=0.45)

# Step 4: Use standardized outputs
for det in prediction.detections:
    print(det.box.xyxy, det.class_name, det.confidence)
```

### Rules

- **Never call** `YOLO("path")`, `RTDETR("path")`, or any direct model constructor.
- **Never auto-download weights.** Weights paths must be explicitly provided.
- **Always call `load_model()`** before `predict()`. Calling `predict()` without loading raises `RuntimeError`.
- `predict()` accepts a single image (NumPy array). Batch inference is NOT supported.
- The adapter returns `ModelPrediction` (not raw model output). All downstream code uses this.
- The only currently implemented adapter is `UltralyticsAdapter` (supports YOLO and RT-DETR via the `ultralytics` package).

---

## 4. Data Structures (from `src/aeronetra/detection/types.py`)

These are the **only** data structures for detection results. Never use raw dicts or tuples.

### `BoundingBox`
- Fields: `xmin`, `ymin`, `xmax`, `ymax` (float, **absolute pixel coordinates**, xyxy format)
- Properties: `width`, `height`, `area`, `center`, `xyxy`

### `Detection`
- Fields: `box` (BoundingBox), `class_id` (int), `class_name` (str), `confidence` (float), `source_model` (str), `image_id` (str)

### `ModelPrediction`
- Fields: `detections` (List[Detection]), `image_width` (int), `image_height` (int), `inference_time_ms` (float)
- Methods: `filter_by_confidence(threshold)`, `filter_by_class(allowed_classes)`
- This is what `adapter.predict()` returns.

### `CountSummary`
- Fields: `image_id` (str), `total_vehicles` (int), `class_counts` (Dict[str, int]), `model_name` (str)

### `InferenceMetadata`
- **All fields are mandatory** when recording experiment results:
  - `model_name`, `package_version`, `weights_path`, `dataset_version`
  - `image_size` (Tuple[int, int]), `confidence_threshold`, `iou_threshold`
  - `seed` (int), `device` (str), `timing_ms` (float)
- Never skip this when recording inference results.

---

## 5. Coordinate Systems

Two coordinate systems exist in this project. Mixing them up is a common agent error.

| System | Format | Range | Used By |
|--------|--------|-------|---------|
| **xyxy (absolute)** | `(xmin, ymin, xmax, ymax)` | Pixel values (0 to image width/height) | `BoundingBox`, `Detection`, drawing functions |
| **YOLO normalized** | `(x_center, y_center, width, height)` | Normalized 0.0–1.0 | `.txt` label files, dataset configs |

### Conversion Functions (in `src/aeronetra/counting/ops.py`)

- `convert_xywh_to_xyxy(x, y, w, h)` → `(xmin, ymin, xmax, ymax)` — converts absolute xywh to xyxy
- `convert_yolo_to_xyxy(x_center, y_center, w, h, img_w, img_h)` → `(xmin, ymin, xmax, ymax)` — converts normalized YOLO to absolute xyxy

**Never reimplement these conversions.** Use the existing functions.

---

## 6. Dataset Handling

### VisDrone (Primary — Implemented)

The converter is in `src/aeronetra/datasets/visdrone.py`.

**VisDrone class IDs and vehicle mapping:**

| VisDrone ID | Category | Included as Vehicle? |
|-------------|----------|---------------------|
| 0 | ignored region | NO — skipped |
| 1 | pedestrian | NO — skipped |
| 2 | people | NO — skipped |
| 3 | bicycle | YES |
| 4 | car | YES |
| 5 | van | YES |
| 6 | truck | YES |
| 7 | tricycle | YES |
| 8 | awning-tricycle | YES |
| 9 | bus | YES |
| 10 | motor | YES |
| 11 | others | NO — skipped |

**Conversion modes:**
- `"merged"` — all vehicle classes → single class `0` ("vehicle")
- `"separate"` — vehicle classes remapped sequentially starting from `0`

**Key functions:**
- `parse_visdrone_row(line)` — parses a single VisDrone annotation line
- `map_category(visdrone_class_id, mode)` — maps VisDrone ID to YOLO class ID (returns `None` for non-vehicle)
- `convert_to_yolo_format(annotations, img_w, img_h, mode)` — converts annotations to normalized YOLO format with boundary clipping
- `convert_dataset(source_dir, output_dir, mode)` — batch converts a full split; **returns a statistics dict** (always capture and log it)

### UAVDT — NOT Implemented

`src/aeronetra/datasets/uavdt.py` is a **stub that raises `NotImplementedError`**. Never fabricate UAVDT support or claim it works. If asked about UAVDT, state clearly that the adapter is not yet implemented.

### Environment Variable

- **`DATASET_DIR`** — set this to point to your dataset root. If unset, falls back to `data/raw/`.
- Use `aeronetra.config.get_data_dir()` to resolve the path. Never hardcode dataset paths.
- Dataset YAML configs use `${DATASET_DIR}` variable substitution.

---

## 7. Configuration Hierarchy

### `configs/inference/inference.yaml`
```yaml
image_size: [640, 640]
confidence_threshold: 0.25
iou_threshold: 0.45
selected_classes: [0, 1, 2, 3, 4, 5, 6]
max_detections: 300
device: "cpu"
```

### `src/aeronetra/config.py`
```python
DEFAULT_CONFIDENCE = 0.5   # ← higher than inference.yaml
DEFAULT_IOU = 0.45
```

**Resolution rule:** YAML config values override `config.py` defaults at runtime. When writing notebooks or scripts, load thresholds from `inference.yaml` rather than using `config.py` defaults directly.

### Important Config Values

| Parameter | YAML Value | config.py Default | Notes |
|-----------|-----------|-------------------|-------|
| `confidence_threshold` | 0.25 | 0.5 | YAML is authoritative for inference |
| `iou_threshold` | 0.45 | 0.45 | Consistent |
| `max_detections` | 300 | — | Ultralytics hardcoded ceiling; affects dense scenes |
| `image_size` | [640, 640] | — | Standard YOLO input size |
| `device` | "cpu" | — | Set to "cuda" if GPU available |

---

## 8. Counting and Drawing (from `src/aeronetra/counting/`)

### `ops.py` — Core Operations

| Function | Purpose |
|----------|---------|
| `convert_xywh_to_xyxy()` | Absolute xywh → xyxy conversion |
| `convert_yolo_to_xyxy()` | Normalized YOLO → absolute xyxy conversion |
| `clip_box(box, img_w, img_h)` | Clip box to image boundaries |
| `filter_by_area(detections, min_area, max_area)` | Remove too-small or too-large boxes |
| `filter_by_aspect_ratio(detections, min_ratio, max_ratio)` | Remove extreme aspect ratios |
| `filter_by_roi(detections, roi)` | Keep only detections inside a Region of Interest |
| `apply_nms(boxes, scores, iou_thresh)` | Non-Maximum Suppression via `cv2.dnn.NMSBoxes` |
| `count_vehicles(detections)` | Returns `(total_count, class_counts_dict)` |

**Warning:** Do not apply NMS on RT-DETR outputs — RT-DETR is end-to-end and already suppresses duplicates. The code has comments about this.

### `drawing.py` — Visualization and Export

| Function | Purpose |
|----------|---------|
| `draw_detections(image, detections)` | Draw bounding boxes with labels |
| `draw_roi(image, roi)` | Draw ROI rectangle |
| `draw_count_summary(image, summary)` | Overlay count text |
| `export_to_json(detections, path)` | Export detections as JSON |
| `export_to_csv(detections, path)` | Export detections as CSV |

---

## 9. Code Organization Rules

- **All reusable logic** goes in `src/aeronetra/`. Never put reusable functions directly in notebooks.
- **Notebooks** call library functions from `src/aeronetra/`. Keep cells short and ordered.
- **Clear notebook outputs** before committing (`jupyter nbconvert --clear-output --inplace notebooks/*.ipynb`).
- **Import convention:** `from aeronetra.detection.adapters import get_model_adapter` (not `from src.aeronetra...`).
- **OpenCV** (`cv2`) is the standard for image loading, bounding-box drawing, geometric filtering, ROI logic, and NMS.

---

## 10. Data and Experiments

- **No Fabrication.** Never fabricate benchmark results, completed training runs, model accuracy, dataset paths, successful tests, or claim stubs are implemented.
- **Distinguish states clearly:**
  - ✅ Implemented and tested
  - ⚠️ Implemented but not tested (e.g., no GPU available)
  - 🔲 Stub / Not implemented
  - ❌ Not executed (missing data, GPU, credentials, or dependencies)
- **No auto-downloads.** Never download datasets or model weights automatically. Require explicit user action (e.g., `--download` flag in scripts).
- **Dataset paths.** Always use `DATASET_DIR` environment variable or `get_data_dir()`. Never hardcode absolute paths.
- **Random seeds.** Use deterministic seeds where practical for reproducibility.
- **Preserve raw data.** Write conversions and outputs into `data/processed/` or `outputs/`, never modify `data/raw/`.
- **Record metadata.** Use `InferenceMetadata` dataclass for every inference run. All fields are mandatory.
- **Validation.** Never claim a model is "best" without measured evidence from the same validation split. Validate bounding boxes and labels before training.

---

## 11. Testing and Quality

```bash
# Run linter
ruff check .

# Run all tests
pytest

# Run a specific test file
pytest tests/test_counting.py -v
```

- Tests live in `tests/` with fixtures in `tests/fixtures/`.
- Fixture files include a sample VisDrone-format label file (`tests/fixtures/labels/0000001.txt`) with edge cases: valid detections, ignored regions, pedestrians, malformed rows, zero-area boxes, out-of-bounds boxes.
- A test image exists at `tests/fixtures/images/0000001.jpg`.
- All new modules in `src/aeronetra/` **must** have accompanying tests.
- Test adapters using mocks — do NOT require real model weights in tests.

### Currently Untested (Known Gaps)

- `src/aeronetra/detection/types.py` — dataclass tests missing
- `src/aeronetra/visualization/plots.py` — no tests
- `src/aeronetra/config.py` — no tests
- `scripts/` — no tests

---

## 12. Secrets and Security

- **Never** place Kaggle API keys, tokens, passwords, or other secrets in source code or markdown files.
- Use environment variables or `.env` file (gitignored) for secrets.
- The `.env.example` file provides a template with placeholder variable names — never fill in real values there.

---

## 13. Things Agents Must NEVER Do

1. ❌ Add frontend frameworks (React, Vue, Angular, Flask templates, Streamlit, Gradio, etc.)
2. ❌ Fabricate benchmark results, accuracy numbers, or training run outputs
3. ❌ Claim `uavdt.py`, `evaluation/`, or `utils/` modules are functional (they are stubs)
4. ❌ Auto-download datasets or model weights without explicit user request
5. ❌ Instantiate models directly (`YOLO("path")`) — always use `get_model_adapter()`
6. ❌ Skip `InferenceMetadata` when recording inference results
7. ❌ Hardcode absolute filesystem paths to datasets or weights
8. ❌ Mix up xyxy (absolute pixels) and YOLO normalized coordinates
9. ❌ Apply NMS to RT-DETR outputs (it's end-to-end, no NMS needed)
10. ❌ Reimplement coordinate conversions that already exist in `counting/ops.py`
11. ❌ Place secrets (API keys, credentials) in source code
12. ❌ Commit notebook outputs or large binary files
13. ❌ Claim a model is "best" without measured evidence from a shared validation split
