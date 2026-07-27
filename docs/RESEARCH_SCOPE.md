# Research Scope

The AeroNetra project is divided into multiple phases to incrementally build capabilities for UAV surveillance and traffic analysis.

## Phase 1: Vehicle detection and image counting
- **Goal:** Detect and accurately count vehicles in static aerial or drone images.
- **Methods:** Object-detection models (e.g., YOLO, RT-DETR), bounding-box processing, and OpenCV for geometry and counting.
- **Focus:** Building a robust pipeline and reproducible research repository.

## Phase 2: Fine-tuning on aerial datasets
- **Goal:** Improve model accuracy specifically for aerial perspectives.
- **Methods:** Transfer learning and fine-tuning using specialized drone imagery datasets.

## Phase 3: Video tracking and unique vehicle counting
- **Goal:** Track vehicles across frames and count unique instances.
- **Methods:** Multi-object tracking (MOT) algorithms, trajectory analysis.

## Phase 4: Geospatial and traffic analytics
- **Goal:** Derive actionable insights from tracking data.
- **Methods:** Speed estimation, density maps, flow analysis, and integration with geospatial coordinates.

## Phase 5: Edge deployment or integration with simulated UAV systems
- **Goal:** Deploy the solution to run efficiently on edge devices or simulated drone hardware.
- **Methods:** Model optimization (TensorRT, ONNX), real-time processing pipelines.
