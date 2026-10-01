---
description: >-
  A modular computer-vision research platform for UAV imagery, vehicle detection,
  image-level counting, model comparison, and reproducible experiments.
icon: drone-front
---

# AeroNetra Computer Vision

AeroNetra is a modular computer-vision research platform for detecting and counting vehicles in aerial and UAV imagery.

The project is designed around one principle:

> **Change the detector without rewriting the rest of the perception pipeline.**

Model-specific behavior is isolated behind adapters, while datasets, filtering, counting, visualization, and experiment code operate on standardized outputs.

{% hint style="info" %}
**Current scope:** static-image vehicle detection and image-level counting. Video tracking, persistent vehicle identities, geospatial analytics, and edge/UAV deployment are planned research phases rather than completed core functionality.
{% endhint %}

## Why AeroNetra?

Aerial vehicle detection is different from ordinary street-level object detection. Objects are often small, densely packed, partially occluded, and viewed from unusual angles.

AeroNetra separates the research problem into explicit layers:

| Layer | Responsibility |
| --- | --- |
| Dataset | Acquire, validate, convert, and organize training data |
| Detection | Run different model families through one adapter interface |
| Post-processing | Confidence, class, geometry, ROI, and architecture-aware filtering |
| Counting | Produce image-level total and per-class vehicle counts |
| Visualization | Inspect predictions and export analysis artifacts |
| Experiments | Keep configurations, evaluation conditions, and comparisons explicit |

This structure makes it easier to reproduce an experiment, swap a model, diagnose a failure, or extend the system without mixing unrelated responsibilities.

## What is implemented?

### Detection

The repository currently provides detector adapters for Ultralytics-based model families, including:

- YOLO-family detectors such as YOLOv8 and YOLO11
- RT-DETR
- A common `ModelPrediction` representation for downstream processing

### Counting

The current counting definition is deliberately simple:

**one valid detection in one image = one counted object.**

Counting utilities support operations such as confidence filtering, class filtering, area/aspect-ratio filtering, ROI filtering, and visualization/export.

{% hint style="warning" %}
Image-level counting is **not** unique-vehicle counting across time. A video system that counts each physical vehicle once requires tracking and persistent identities.
{% endhint %}

### Dataset pipeline

VisDrone is the primary implemented aerial dataset.

The repository includes:

- VisDrone annotation parsing
- vehicle-class mapping
- YOLO-format conversion
- dataset validation
- reusable dataset configuration
- test fixtures for conversion logic

UAVDT and later datasets are planned extensions unless explicitly marked as implemented in the repository documentation.

## Architecture

~~~
flowchart LR
    A[Aerial / UAV Image] --> B[Dataset Validation]
    B --> C[Detector Adapter]
    C --> D[Standardized ModelPrediction]
    D --> E[Post-processing]
    E --> F[Vehicle Counting]
    F --> G[Visualization / Export]
    G --> H[Experiment Analysis]

    C --> Y[YOLO family]
    C --> R[RT-DETR]
~~~

The important boundary is the detector adapter.

A model produces raw framework-specific output. AeroNetra normalizes that output into shared prediction objects so the rest of the pipeline does not need to know whether the detector is YOLO-based or transformer-based.

## Repository structure

~~~
AeroNetra-computervision/
├── src/
│   └── aeronetra/
│       ├── detection/        # Adapters, prediction types, model interfaces
│       ├── counting/         # Filtering, counting, drawing, export
│       ├── datasets/         # Dataset parsing and conversion
│       └── visualization/    # Visualization helpers
│
├── configs/                  # Dataset and inference configuration
├── notebooks/                # Local experiments and inference workflows
├── kaggle/                   # GPU-oriented preparation, training, evaluation
├── scripts/                  # Dataset download and validation utilities
├── tests/                    # Automated tests and fixtures
├── docs/                     # Detailed project documentation
└── px4_ros2_jazzy_gazebo_harmonic_sitl/
                             # UAV simulation integration documentation
~~~

## Quick start

### 1. Clone the repository

~~~
git clone https://github.com/Pratyush061/AeroNetra-computervision.git
cd AeroNetra-computervision
~~~

### 2. Create a Python environment

AeroNetra currently targets Python 3.11+.

~~~
python -m venv .venv
~~~

Activate it:

~~~
# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
~~~

### 3. Install dependencies

~~~
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .
~~~

### 4. Configure the environment

~~~
cp .env.example .env
~~~

Set the dataset/output locations appropriate for your machine. See [Environment Setup](docs/ENVIRONMENT_SETUP.md) for the complete configuration reference.

### 5. Verify the installation

~~~
python -c "import aeronetra; print(aeronetra.__version__)"
ruff check .
pytest
~~~

## Run inference

AeroNetra exposes a common detector-adapter interface.

~~~python
from aeronetra.detection.adapters import get_model_adapter

adapter = get_model_adapter(
    model_name="YOLOv8",
    weights_path="outputs/models/yolov8n.pt",
    class_names={
        0: "car",
        1: "van",
        2: "truck",
        3: "tricycle",
        4: "awning-tricycle",
        5: "bus",
        6: "motor",
        7: "bicycle",
    },
    device="cpu",
)

adapter.load_model()
prediction = adapter.predict(
    image,
    conf_thresh=0.25,
    iou_thresh=0.45,
)
~~~

The returned `ModelPrediction` can then be passed through shared filtering and counting code:

~~~python
filtered = prediction.filter_by_confidence(0.5)

from aeronetra.counting.ops import count_vehicles
from aeronetra.counting.drawing import draw_detections

total, by_class = count_vehicles(filtered.detections)
annotated = draw_detections(image.copy(), filtered.detections)

print("Total vehicles:", total)
print("Per-class:", by_class)
~~~

For the architecture, lifecycle, failure modes, and reproducibility requirements, see [Model Inference Guide](docs/MODEL_INFERENCE.md).

## Train on Kaggle

Training and heavier evaluation are designed to run on GPU-capable environments such as Kaggle.

The repository keeps the GPU workflow separate from the local package so local development can focus on reusable code, validation, and inference.

~~~
Kaggle
  │
  ├── 01_dataset_preparation
  │        ↓
  │   YOLO-format dataset
  │        ↓
  ├── 02_model_training
  │        ↓
  │   trained weights
  │        ↓
  ├── 03_model_evaluation
  │        ↓
  │   metrics / plots
  │        ↓
  └── 04_inference_comparison
           ↓
      visual + speed analysis
~~~

See the dedicated [Kaggle workflow guide](kaggle/README.md).

## Datasets

VisDrone is the primary implemented dataset.

The dataset pipeline follows this pattern:

~~~
Raw dataset
    ↓
Validation
    ↓
Class mapping
    ↓
YOLO conversion
    ↓
Processed dataset
    ↓
Training / evaluation
~~~

The repository keeps raw data separate from processed artifacts so conversion steps remain explicit and repeatable.

See [Datasets Guide](docs/DATASETS.md).

## Model comparison

AeroNetra is intended for controlled comparisons rather than informal model screenshots.

When comparing models, keep the evaluation conditions explicit:

| Parameter | Record it? |
| --- | ---: |
| Dataset and split | ✅ |
| Model architecture | ✅ |
| Model weights/version | ✅ |
| Image size | ✅ |
| Confidence threshold | ✅ |
| IoU threshold | ✅ |
| Device / hardware | ✅ |
| Inference latency | ✅ |
| Precision / recall | ✅ |
| mAP@50 | ✅ |
| mAP@50-95 | ✅ |
| Counting error | ✅ |

A fair comparison also needs architecture-aware post-processing. For example, RT-DETR should not automatically be forced through a YOLO-style external NMS path.

See [Model Comparison](docs/MODEL_COMPARISON.md).

## Reproducibility

AeroNetra treats reproducibility as part of the implementation, not as a final reporting step.

For a meaningful experiment, record:

- the exact dataset and split
- class mapping
- model family and weights
- image size
- confidence and IoU thresholds
- filtering/ROI rules
- device and runtime environment
- evaluation metrics
- inference timing
- generated artifacts

{% hint style="warning" %}
Do not describe a model as “best” from a single visual example or from results produced under different data, thresholds, splits, or post-processing rules.
{% endhint %}

## Documentation

| Topic | Guide |
| --- | --- |
| Environment setup | [docs/ENVIRONMENT_SETUP.md](docs/ENVIRONMENT_SETUP.md) |
| Dataset lifecycle | [docs/DATASETS.md](docs/DATASETS.md) |
| Model inference | [docs/MODEL_INFERENCE.md](docs/MODEL_INFERENCE.md) |
| Model comparison | [docs/MODEL_COMPARISON.md](docs/MODEL_COMPARISON.md) |
| Counting methodology | [docs/COUNTING_METHODOLOGY.md](docs/COUNTING_METHODOLOGY.md) |
| Research scope | [docs/RESEARCH_SCOPE.md](docs/RESEARCH_SCOPE.md) |
| Kaggle notebooks | [kaggle/README.md](kaggle/README.md) |

## Development

Run the validation suite before submitting changes:

~~~
ruff check .
pytest
~~~

The project uses Ruff for linting and pytest for automated tests. Notebook files are intentionally excluded from Ruff's default repository-wide linting configuration.

For changes to detection behavior, dataset conversion, or counting logic, add or update tests alongside the implementation.

## Research roadmap

~~~
flowchart LR
    P1[Phase 1<br/>Static Detection & Counting]
    --> P2[Phase 2<br/>Aerial Fine-tuning]
    P2 --> P3[Phase 3<br/>Video Tracking]
    P3 --> P4[Phase 4<br/>Traffic & Geospatial Analytics]
    P4 --> P5[Phase 5<br/>Edge / UAV Integration]
~~~

| Phase | Focus | Status |
| --- | --- | --- |
| 1 | Static detection and image-level counting | Current |
| 2 | Aerial fine-tuning and model improvement | Planned |
| 3 | Video tracking and unique vehicle counts | Planned |
| 4 | Traffic and geospatial analytics | Planned |
| 5 | UAV / edge integration | Planned |

The roadmap is intentionally phased. Later capabilities should build on measurable detection and counting behavior rather than being presented as already implemented.

## Project status

AeroNetra is an active research codebase.

The repository contains implemented detection/counting components, dataset tooling, tests, local notebooks, and a Kaggle experimentation workflow. Some future integrations and dataset modules remain incomplete by design.

## Contributing

Contributions are welcome, especially improvements that make the pipeline more reproducible, testable, and easier to extend.

For a useful contribution:

1. Keep model-specific logic inside adapters.
2. Keep raw datasets immutable.
3. Add tests for behavior that changes.
4. Document new assumptions and configuration.
5. Avoid reporting unverified benchmark results as established facts.

## License

AeroNetra is released under the [MIT License](LICENSE).

## Acknowledgements

AeroNetra builds on the work of the computer-vision and open-source communities, including the datasets and model frameworks used by the project.

Please review the license and usage terms of upstream datasets and model dependencies before redistribution or commercial deployment.

---

<p align="center">
  <sub>Built for reproducible UAV computer-vision research.</sub>
</p>
