---
description: >-
  AeroNetra is a reproducible computer-vision research platform for UAV-based
  vehicle detection, counting, model comparison, and simulation-oriented
  experimentation.
---

# AeroNetra Computer Vision

AeroNetra is a research-focused computer-vision project for **detecting and counting vehicles in aerial and UAV imagery**. The project separates reusable Python code, dataset tooling, model adapters, experiments, notebooks, and simulation work so that results remain understandable and reproducible.

{% hint style="info" %}
**Current scope:** static-image vehicle detection and image-level counting. Video tracking, unique cross-frame counting, geospatial analytics, and edge deployment are later phases.
{% endhint %}

## System at a glance

```mermaid
flowchart LR
    A[Aerial / UAV Image] --> B[Dataset & Image Validation]
    B --> C[Detector Adapter]
    C --> D[Standardized ModelPrediction]
    D --> E[Confidence / Class / ROI Filters]
    E --> F[Vehicle Counting]
    F --> G[Visualization & Export]
    G --> H[Experiment Comparison]

    C -. model backends .-> Y[YOLO variants]
    C -. model backends .-> R[RT-DETR]
```

The key design idea is simple: **models may differ, but downstream code should not have to.** Every supported detector is normalized into the same prediction structures before counting and visualization.

## What the repository contains

| Area                                   | Purpose                                                       |
| -------------------------------------- | ------------------------------------------------------------- |
| `src/aeronetra/detection/`             | Detector adapters and standardized prediction types           |
| `src/aeronetra/counting/`              | Filtering, NMS, ROI logic, counting, drawing and export       |
| `src/aeronetra/datasets/`              | Dataset parsing and conversion; VisDrone is implemented       |
| `src/aeronetra/visualization/`         | Plotting and visual analysis utilities                        |
| `configs/`                             | Dataset and inference configuration                           |
| `notebooks/`                           | Local exploration and inference workflow                      |
| `kaggle/`                              | GPU-oriented preparation, training, evaluation and comparison |
| `scripts/`                             | Dataset download and validation utilities                     |
| `tests/`                               | Automated tests and fixtures                                  |
| `px4_ros2_jazzy_gazebo_harmonic_sitl/` | PX4 + ROS 2 + Gazebo simulation documentation                 |

## End-to-end research workflow

```mermaid
flowchart TD
    A[Raw VisDrone data] --> B[Validate annotations]
    B --> C[Convert to training format]
    C --> D[Train / fine-tune on Kaggle GPU]
    D --> E[Download trained weights]
    E --> F[Load through get_model_adapter]
    F --> G[Run inference]
    G --> H[Filter detections]
    H --> I[Count vehicles]
    I --> J[Visualize results]
    J --> K[Record metadata & compare models]
```

## Quick start

```bash
python -m venv venv
source venv/bin/activate   # Linux/macOS
# venv\Scripts\activate   # Windows

pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .
```

Configure dataset paths:

```bash
cp .env.example .env
```

Then verify the package:

```bash
python -c "import aeronetra; print(aeronetra.__version__)"
ruff check .
pytest
```

## Choose your path

<table data-view="cards"><thead><tr><th></th><th></th></tr></thead><tbody><tr><td><strong>Set up the project</strong></td><td><a href="docs/ENVIRONMENT_SETUP.md">Environment Setup</a></td></tr><tr><td><strong>Understand the data</strong></td><td><a href="docs/DATASETS.md">Datasets Guide</a></td></tr><tr><td><strong>Run a detector</strong></td><td><a href="docs/MODEL_INFERENCE.md">Model Inference Guide</a></td></tr><tr><td><strong>Understand counting</strong></td><td><a href="docs/COUNTING_METHODOLOGY.md">Counting Methodology</a></td></tr><tr><td><strong>Compare architectures</strong></td><td><a href="docs/MODEL_COMPARISON.md">Model Comparison</a></td></tr><tr><td><strong>See the roadmap</strong></td><td><a href="docs/RESEARCH_SCOPE.md">Research Scope</a></td></tr></tbody></table>

## Research principles

* **Reproducibility over impressive-looking demos.** Parameters, dataset split, model weights and timing should be recorded.
* **No fabricated benchmarks.** A model is not “best” until it is measured under the same evaluation conditions.
* **Raw data remains immutable.** Transformations go to processed directories.
* **Model-specific behavior stays inside adapters.** Counting code consumes standardized predictions.
* **Phase boundaries matter.** Image counting is not the same as multi-object tracking.

## Current roadmap

```mermaid
flowchart LR
    P1[Phase 1<br/>Static Detection & Counting] --> P2[Phase 2<br/>Aerial Fine-tuning]
    P2 --> P3[Phase 3<br/>Video Tracking]
    P3 --> P4[Phase 4<br/>Traffic & Geospatial Analytics]
    P4 --> P5[Phase 5<br/>Edge / UAV Integration]
```

{% hint style="warning" %}
Some modules are intentionally incomplete. UAVDT support is stubbed, and later-phase tracking/analytics capabilities should not be presented as implemented functionality.
{% endhint %}
