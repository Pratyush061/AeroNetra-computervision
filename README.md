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
