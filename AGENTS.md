# Instructions for Coding Agents

This repository is **AeroNetra**, a computer-vision research project for UAV/drone-based vehicle detection and counting. This file is the authoritative reference for AI coding agents. Every instruction below is grounded in the actual codebase — follow them exactly.

***

## 1. Core Directives

* **Research software only.** This is NOT a website, mobile app, dashboard, API product, or SaaS. Never add frontend frameworks, web servers, or UI code unless explicitly requested.
* **Inspect before editing.** Always read existing files before modifying them. Preserve useful code and avoid unnecessary overwrites or refactors.
* **Small, reviewable changes.** Prefer smaller, iterative modifications over large rewrites.
* **Current phase is Phase 1** — static image vehicle detection and counting. Do NOT implement video tracking, geospatial analytics, or edge deployment unless explicitly asked.
* **Verified simulation documentation exists.** Before changing PX4/ROS 2/Gazebo camera integration, read `px4_ros2_jazzy_gazebo_harmonic_sitl/docs/verified-yolo-camera-pipeline.md` and its troubleshooting guide.

***

## 2. Project Structure

```
├── AGENTS.md
├── README.md
├── DEVELOPER_GUIDE.md
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── src/aeronetra/
│   ├── config.py
│   ├── detection/
│   │   ├── adapters.py
│   │   └── types.py
│   ├── counting/
│   │   ├── ops.py
│   │   └── drawing.py
│   ├── datasets/
│   │   ├── visdrone.py
│   │   └── uavdt.py
│   ├── visualization/
│   ├── evaluation/
│   └── utils/
├── configs/
├── notebooks/
├── kaggle/
├── scripts/
├── tests/
├── data/
├── outputs/
├── docs/
└── px4_ros2_jazzy_gazebo_harmonic_sitl/
    ├── README.md
    ├── docs/
    │   ├── continue-existing-setup.md
    │   ├── environment-report.md
    │   ├── run-simulation.md
    │   ├── verified-yolo-camera-pipeline.md
    │   └── troubleshooting.md
    ├── scripts/
    └── ros2_ws/
```

### Stubs that are not implemented

Never fabricate implementations or claim these work:

| Path                              | Status                             |
| --------------------------------- | ---------------------------------- |
| `src/aeronetra/datasets/uavdt.py` | Stub; raises `NotImplementedError` |
| `src/aeronetra/evaluation/`       | Empty / placeholder                |
| `src/aeronetra/utils/`            | Empty / placeholder                |
| `configs/experiments/`            | No experiment configs yet          |
| `configs/models/`                 | No model configs yet               |

***

## 3. Core Model Adapter Contract

Reusable AeroNetra detection code **must** use the model adapter interface.

```python
from aeronetra.detection.adapters import get_model_adapter

adapter = get_model_adapter(
    model_name="YOLOv8",
    weights_path="path/to/weights.pt",
    class_names={0: "vehicle"},
    device="cpu",
)
adapter.load_model()
prediction = adapter.predict(
    image_array,
    conf_thresh=0.25,
    iou_thresh=0.45,
)
```

Rules:

* Do not directly instantiate YOLO/RT-DETR inside `src/aeronetra/`, standard notebooks, dataset experiments, or reusable library code.
* Do not auto-download model weights.
* Call `load_model()` before `predict()`.
* Consume `ModelPrediction`, not raw model output, in downstream reusable code.
* The implemented adapter is `UltralyticsAdapter`.

### Narrow simulation-harness exception

The tested ROS 2/Gazebo integration uses a standalone `yolo_car_detector.py` harness that loads the VisDrone-trained model directly with Ultralytics. This exception exists **only** to reproduce the already-tested live simulation integration documented under:

```
px4_ros2_jazzy_gazebo_harmonic_sitl/docs/verified-yolo-camera-pipeline.md
```

It does **not** change the core AeroNetra architecture. Do not copy the direct-constructor pattern into `src/aeronetra/`, normal notebooks, training/evaluation code, or new reusable modules. If the simulation harness is later productized, refactor it to consume AeroNetra's adapter layer rather than expanding the exception.

***

## 4. Detection Data Structures

Use the existing structures from `aeronetra.detection.types`:

* `BoundingBox`: absolute pixel coordinates in `xyxy` order; validates coordinate ordering.
* `Detection`: bounding box, class ID/name, confidence, model and image identity.
* `ModelPrediction`: list of detections plus image dimensions and inference timing.
* `CountSummary`: image-level total and per-class counts.
* `InferenceMetadata`: required experiment metadata including model, weights, dataset version, thresholds, image size, seed, device and timing.

`ModelPrediction.filter_by_confidence()` and `filter_by_class()` return **new** prediction objects; they do not mutate the source prediction.

***

## 5. Coordinate Systems

| System          | Format                                | Range     | Used by                               |
| --------------- | ------------------------------------- | --------- | ------------------------------------- |
| Absolute        | `(xmin, ymin, xmax, ymax)`            | Pixels    | `BoundingBox`, detections and drawing |
| YOLO normalized | `(x_center, y_center, width, height)` | `0.0–1.0` | YOLO label files                      |

Use existing conversion helpers in `src/aeronetra/counting/ops.py`. Do not reimplement coordinate conversions.

***

## 6. Dataset Rules

### VisDrone

VisDrone is the primary implemented dataset. The converter lives in `src/aeronetra/datasets/visdrone.py`.

Vehicle categories are VisDrone IDs 3–10: bicycle, car, van, truck, tricycle, awning-tricycle, bus and motor. Ignored regions, pedestrians, people and `others` are excluded from the vehicle mapping.

Supported conversion modes:

* `merged`: all vehicle categories become one `vehicle` class.
* `separate`: vehicle categories are remapped to separate sequential class IDs.

Always capture the statistics dictionary returned by `convert_dataset()`.

### UAVDT

`src/aeronetra/datasets/uavdt.py` is not implemented. Do not claim UAVDT support works.

### Paths

Use `DATASET_DIR` / `get_data_dir()` for datasets and `OUTPUT_DIR` / `get_output_dir()` for outputs. Do not hardcode developer-specific dataset or model paths in reusable library code.

***

## 7. Configuration Rules

`configs/inference/inference.yaml` is the runtime reference for standard inference parameters. Current values include:

```yaml
image_size: [640, 640]
confidence_threshold: 0.25
iou_threshold: 0.45
selected_classes: [0, 1, 2, 3, 4, 5, 6]
max_detections: 300
device: "cpu"
```

When a YAML inference configuration is loaded, use it instead of silently falling back to unrelated defaults in `config.py`.

Simulation-specific diagnostic values such as `YOLO_CONF=0.15`, `YOLO_IMGSZ=416`, or frame skipping belong to the verified PX4/Gazebo integration workflow and must not silently become the general research defaults.

***

## 8. Counting and Drawing

Use existing functions in `src/aeronetra/counting/` for coordinate conversion, clipping, area/aspect-ratio filtering, ROI filtering, NMS, counting, drawing, and JSON/CSV export.

**Do not apply additional NMS to RT-DETR output.** RT-DETR is end-to-end and should not receive the YOLO-specific suppression path.

***

## 9. Code Organization

* Reusable logic belongs in `src/aeronetra/`.
* Notebooks should call library functions instead of duplicating reusable logic.
* Use package imports such as `from aeronetra...`, not `from src.aeronetra...`.
* Clear notebook outputs before committing.
* Keep model weights, datasets and generated outputs out of version control.
* Add tests for new reusable modules.

***

## 10. Reproducibility and Evidence

* Never fabricate benchmark results, model accuracy, completed training runs, successful tests, or dataset paths.
* Distinguish **implemented and tested**, **implemented but untested**, **stub**, and **not executed** states.
* Preserve raw data; write conversions to processed/output locations.
* Use deterministic seeds where practical.
* Record inference metadata.
* Never call a model “best” based on anecdotal single-image output.

The PX4/Gazebo CV workflow is explicitly marked **tested** because it is based on the recorded working development sequence. Do not extend the “tested” label to unexecuted variations.

***

## 11. Testing and Quality

```bash
ruff check .
pytest
pytest tests/test_counting.py -v
```

Tests live under `tests/`. Adapter tests should use mocks rather than requiring large model weights.

***

## 12. Secrets and Security

* Never commit Kaggle credentials, tokens, passwords or API keys.
* Use environment variables or ignored `.env` files.
* Keep `.env.example` free of real credentials.

***

## 13. Verified PX4 / ROS 2 / Gazebo Rules

The tested camera pipeline is:

```mermaid
flowchart LR
    A[Gazebo IMX214] --> B[ros_gz_image]
    B --> C[ROS 2 Image]
    C --> D[YOLO simulation harness]
    D --> E[/vision/annotated]
    E --> F[rqt_image_view]
```

Agents working on this integration must follow these rules:

1. `MicroXRCEAgent` is for PX4 telemetry/control; it does **not** bridge Gazebo camera images.
2. Use `ros_gz_image image_bridge` for the IMX214 camera path.
3. A camera-only CV test does not require QGroundControl or Micro XRCE-DDS.
4. Topic variables are shell-local. Re-discover `GZ_IMAGE_TOPIC` / `ROS_IMAGE_TOPIC` in the terminal where they are used.
5. If the Gazebo image topic is absent, stop before running the detector.
6. Validate frame transport before debugging model accuracy.
7. `/vision/annotated` is the detector output; the raw IMX214 topic will not contain bounding boxes.
8. The VisDrone model has a simulation-to-real domain gap. Camera scale, angle, texture and confidence threshold matter.
9. CPU fallback values (`YOLO_IMGSZ=416`, `PROCESS_EVERY_N_FRAMES=2`) are performance tradeoffs, not universal defaults.
10. The observed `NAV_DLL_ACT 0` change is a **local SITL-only** arming workaround. Never generalize it to physical aircraft.

Read `px4_ros2_jazzy_gazebo_harmonic_sitl/docs/verified-yolo-camera-pipeline.md` before modifying this flow.

***

## 14. Things Agents Must Never Do

1. Add unrelated frontend/web application code.
2. Fabricate results, accuracy or test status.
3. Claim stub modules are implemented.
4. Auto-download large datasets/model weights without explicit instruction.
5. Bypass `get_model_adapter()` in core/reusable AeroNetra code; the documented ROS simulation harness is the only narrow exception.
6. Skip experiment metadata when recording results.
7. Hardcode developer-specific dataset/weight paths into reusable library code.
8. Mix absolute `xyxy` and normalized YOLO coordinates.
9. Apply NMS to RT-DETR output.
10. Reimplement existing coordinate conversions.
11. Commit secrets, model weights, datasets, notebook outputs or other large generated artifacts.
12. Treat a simulation failsafe workaround as a real-flight recommendation.
