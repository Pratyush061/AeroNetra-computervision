# AeroNetra

AeroNetra is a computer-vision research project for UAV and drone-based vehicle detection and counting. The repository is structured to support rigorous, reproducible experiments on aerial imagery.

> **For AI coding agents:** See [AGENTS.md](AGENTS.md) for authoritative coding rules, data structure contracts, and anti-hallucination guidelines.

## Current Phase

**Phase 1 — Static Image Vehicle Detection and Counting**

Detect and count vehicles in individual aerial/drone images using object-detection models (YOLO variants, RT-DETR), bounding-box processing, and OpenCV utilities.

## Repository Structure

```
├── src/aeronetra/          ← Reusable Python library (detection, counting, datasets, visualization)
│   ├── detection/          ← Model adapters (BaseDetector, UltralyticsAdapter) and data types
│   ├── counting/           ← Coordinate conversions, filtering, NMS, drawing, export
│   ├── datasets/           ← Dataset parsers and converters (VisDrone implemented, UAVDT stub)
│   └── visualization/      ← Distribution plots
├── configs/                ← YAML configs for datasets, inference, experiments, models
├── notebooks/              ← Jupyter notebooks 00–08 (environment → evaluation progression)
├── scripts/                ← CLI tools (dataset download, validation)
├── tests/                  ← pytest tests with fixtures
├── docs/                   ← Detailed documentation
├── data/                   ← Datasets (gitignored)
└── outputs/                ← Generated artifacts (gitignored)
```

## Quick Start

### 1. Environment Setup

```bash
# Create and activate a Python 3.11 virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env to set DATASET_DIR to your dataset root path
```

### 3. Verify Installation

```bash
python -c "import aeronetra; print(aeronetra.__version__)"
```

### 4. Run Notebooks

```bash
jupyter notebook
```

Follow the numbered progression: `00_environment_check.ipynb` → `08_model_evaluation.ipynb`.

### 5. Run Tests and Linting

```bash
ruff check .
pytest
```

## Datasets

Raw datasets should be placed in `data/raw/` or configured via the `DATASET_DIR` environment variable. See [docs/DATASETS.md](docs/DATASETS.md) for supported datasets, class mappings, and directory layouts.

**Do not commit dataset files to version control** — they are large binary files tracked in `.gitignore`.

## Workflow: Local + Kaggle GPU

AeroNetra supports two complementary workflows:

### **Local Workflow** (No GPU Required)
- Exploratory notebooks (00–02): environment check, dataset exploration, OpenCV counting
- Small-scale inference and visualization
- Runs on CPU; fast enough for prototyping
- **Location:** `notebooks/` (00–06 for inference testing, 07–08 not yet completed)

### **Kaggle GPU Workflow** (Recommended for Training)
- **Problem:** Training and evaluation require a GPU (T4 x2 free on Kaggle).
- **Solution:** 4 specialized self-contained notebooks in `kaggle/` that run on Kaggle GPUs:
  1. **01_dataset_preparation** — Convert VisDrone → YOLO format
  2. **02_model_training** — Fine-tune YOLOv8n, YOLO11n, RT-DETR-l (50/50/30 epochs)
  3. **03_model_evaluation** — mAP@50, mAP@50-95, precision, recall benchmarks
  4. **04_inference_comparison** — Side-by-side multi-model inference visualizations
- **Workflow:** Train on Kaggle → Download weights → Use locally via `get_model_adapter()`
- **See:** [kaggle/README.md](kaggle/README.md) for full setup instructions

## Recent Code Improvements (July 2026)

✅ **Import Paths Fixed**
- All imports changed from `from src.aeronetra...` to `from aeronetra...` (standard package imports)
- Works correctly after `pip install -e .`

✅ **Package Exports**
- Root `__init__.py` now exports public API: `BoundingBox`, `Detection`, `ModelPrediction`, `CountSummary`, `InferenceMetadata`, `get_model_adapter`
- All 6 subpackages have `__init__.py` with re-exports for cleaner imports

✅ **Data Structure Safety**
- `BoundingBox` now validates coordinates on creation (raises `ValueError` if xmin > xmax or ymin > ymax)
- `ModelPrediction.filter_by_confidence()` and `filter_by_class()` now return new instances instead of mutating in-place

✅ **Config Improvements**
- Added `load_yaml()` helper to load any YAML config file
- Added `load_inference_config()` shortcut for `configs/inference/inference.yaml`
- Added `get_output_dir()` function (respects `OUTPUT_DIR` env var)

✅ **Bug Fixes**
- Fixed NMS in `ops.py`: removed `int()` casting that lost float precision on box coordinates
- Fixed `validate_dataset.py`: early returns now return the stats dict (not `None`)
- Removed dead code in `visdrone.py` — cleaner `map_category()` implementation
- Added logging to adapters, ops, visdrone modules

✅ **Testing**
- All test imports updated to use standard `aeronetra` package paths
- `test_counting.py` updated for non-mutating filter methods
- `test_config.py` expanded with YAML loader tests
- All Pylance checks pass (no errors in src/ or tests/)

## Key Documentation

| Document | Description |
|----------|-------------|
| [AGENTS.md](AGENTS.md) | Authoritative rules for AI coding agents |
| [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) | Human developer onboarding |
| [docs/ENVIRONMENT_SETUP.md](docs/ENVIRONMENT_SETUP.md) | Detailed environment configuration |
| [docs/DATASETS.md](docs/DATASETS.md) | Dataset formats, class mappings, directory layouts |
| [docs/MODEL_INFERENCE.md](docs/MODEL_INFERENCE.md) | Model adapter interface and inference pipeline |
| [docs/MODEL_COMPARISON.md](docs/MODEL_COMPARISON.md) | Comparing YOLO vs RT-DETR fairly |
| [docs/COUNTING_METHODOLOGY.md](docs/COUNTING_METHODOLOGY.md) | Counting challenges and mitigation strategies |
| [docs/NOTEBOOK_GUIDE.md](docs/NOTEBOOK_GUIDE.md) | Notebook conventions and progression |
| [docs/EXPERIMENT_GUIDE.md](docs/EXPERIMENT_GUIDE.md) | Recording experiment metadata |
| [docs/RESEARCH_SCOPE.md](docs/RESEARCH_SCOPE.md) | Project phases and roadmap |
| [docs/LIMITATIONS.md](docs/LIMITATIONS.md) | Known limitations and constraints |

## Planned Progression

| Phase | Focus | Status |
|-------|-------|--------|
| **Phase 1** | Vehicle detection and image counting | 🟢 Current |
| **Phase 2** | Fine-tuning on aerial datasets | 🔲 Future |
| **Phase 3** | Video tracking and unique vehicle counting | 🔲 Future |
| **Phase 4** | Geospatial and traffic analytics | 🔲 Future |
| **Phase 5** | Edge deployment or simulated UAV integration | 🔲 Future |

## Excluded Files

Large files, datasets, trained weights, credentials, notebook outputs, and generated images are intentionally excluded from version control via `.gitignore`.
