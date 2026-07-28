# Developer Guide for AeroNetra

Welcome to AeroNetra, a research project for UAV and drone-based vehicle detection and counting. This guide covers environment setup, development conventions, and how to work with the codebase.

> **For AI coding agents:** See [AGENTS.md](AGENTS.md) instead — it contains authoritative rules, data structure contracts, and code patterns.

---

## 1. Prerequisites

- **Python 3.11** (strictly required — the development environment and CI target this version).
- A virtual environment tool (`venv` or `conda`).
- Git for version control.
- (Optional) NVIDIA GPU with CUDA for model inference and training.
- (Optional) Kaggle CLI for dataset downloads (`pip install kaggle`).

---

## 2. Environment Setup

### Step 2.1: Clone the Repository
```bash
git clone <repository_url>
cd AeroNetra-computervision
```

### Step 2.2: Create a Virtual Environment

**Using venv:**
```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
```

**Using conda:**
```bash
conda create -n aeronetra python=3.11
conda activate aeronetra
```

### Step 2.3: Install Dependencies
```bash
pip install -r requirements.txt       # Runtime deps (torch, ultralytics, opencv, etc.)
pip install -r requirements-dev.txt   # Dev deps (pytest, ruff)
pip install -e .                      # Install aeronetra package in editable mode
```

### Step 2.4: Configure Environment Variables
```bash
cp .env.example .env
```

Edit `.env` and set at minimum:
- `DATASET_DIR` — absolute path to your dataset root (e.g., `C:\datasets\VisDrone` or `/data/visdrone`)

If `DATASET_DIR` is not set, the code falls back to `data/raw/` in the project root.

> **Never** place Kaggle API keys or other secrets in source code. Use `.env` (which is gitignored) or system environment variables.

### Step 2.5: Verify Installation
```bash
python -c "import aeronetra; print(aeronetra.__version__)"
```

---

## 3. Code Conventions

### Import Paths
Always import from the installed package, not the filesystem path:
```python
# CORRECT
from aeronetra.detection.adapters import get_model_adapter
from aeronetra.detection.types import Detection, ModelPrediction
from aeronetra.counting.ops import count_vehicles

# INCORRECT — never use src. prefix
from src.aeronetra.detection.adapters import get_model_adapter
```

### Model Adapter Pattern
All model interactions go through the adapter interface. See [docs/MODEL_INFERENCE.md](docs/MODEL_INFERENCE.md) for details.

```python
adapter = get_model_adapter("YOLOv8", weights_path, class_names, device)
adapter.load_model()                    # Must call before predict()
prediction = adapter.predict(image)     # Returns ModelPrediction
```

Never instantiate models directly (e.g., `YOLO("path")`).

### Data Structures
Use dataclasses from `src/aeronetra/detection/types.py` for all detection results:
- `BoundingBox` — xyxy absolute pixel coordinates
- `Detection` — single detected object
- `ModelPrediction` — complete inference output with filter methods
- `CountSummary` — counting results per image
- `InferenceMetadata` — **all fields mandatory** for experiment tracking

### OpenCV
Use `cv2` (OpenCV) for image loading, bounding-box drawing, geometric filtering, ROI logic, and NMS (`cv2.dnn.NMSBoxes`).

---

## 4. Jupyter Notebooks

Notebooks are in `notebooks/` and follow a numbered progression (00–08). Launch with:
```bash
jupyter notebook
```

### Notebook Rules
- **Call library functions** from `src/aeronetra/` — do not duplicate core logic in notebook cells.
- **Keep cells short** and logically ordered.
- **Model inference notebooks** (03–06) are independent per architecture. Load weights explicitly without training.
- **Never auto-download** model weights or datasets in notebook cells.
- **Clear outputs before committing:**
  ```bash
  jupyter nbconvert --clear-output --inplace notebooks/*.ipynb
  ```

---

## 5. Working with Data and Experiments

### Dataset Management
- Place raw datasets in `data/raw/` or set `DATASET_DIR` environment variable.
- Use `aeronetra.config.get_data_dir()` to resolve the dataset path — never hardcode.
- Preserve raw data; write conversions to `data/processed/` and outputs to `outputs/`.

### Recording Experiment Metadata
Use the `InferenceMetadata` dataclass from `src/aeronetra/detection/types.py` for every inference run:

```python
from aeronetra.detection.types import InferenceMetadata

metadata = InferenceMetadata(
    model_name="YOLOv8n",
    package_version="8.0.0",
    weights_path="outputs/models/yolov8n.pt",
    dataset_version="VisDrone2019-DET-val",
    image_size=(640, 640),
    confidence_threshold=0.25,
    iou_threshold=0.45,
    seed=42,
    device="cuda",
    timing_ms=15.3
)
```

All fields are mandatory. Never fabricate benchmark results or claim a model is "best" without measured evidence from the same validation split.

### Dataset Validation
Before training, validate your dataset with:
```bash
python scripts/validate_dataset.py --dataset-dir <path> --num-classes <n>
```

This checks for missing image-label pairs, malformed labels, zero-area boxes, out-of-bounds coordinates, and other common issues.

---

## 6. Testing and Linting

```bash
# Linter
ruff check .

# All tests
pytest

# Specific test file with verbose output
pytest tests/test_counting.py -v
```

- All new modules in `src/aeronetra/` **must** have accompanying tests in `tests/`.
- Test adapters using **mocks** — do not require real model weights in tests.
- Fixtures live in `tests/fixtures/` (sample VisDrone labels, test images).

---

## 7. What NOT to Do

- ❌ Add frontend frameworks, web servers, or UI code
- ❌ Fabricate benchmark results or training run outputs
- ❌ Auto-download datasets or model weights
- ❌ Hardcode absolute filesystem paths
- ❌ Commit notebook outputs or large binary files
- ❌ Place secrets (API keys, credentials) in source code
- ❌ Claim stubs (`uavdt.py`, `evaluation/`, `utils/`) are functional

By following these guidelines, you help maintain a clean, reproducible research repository.
