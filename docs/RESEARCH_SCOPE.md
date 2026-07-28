# Research Scope

The AeroNetra project is divided into multiple phases to incrementally build capabilities for UAV surveillance and traffic analysis.

---

## Phase Overview

| Phase | Focus | Status | GPU Required |
|:-----:|-------|:------:|:------------:|
| **1** | Vehicle detection and image counting | 🟢 **Current** | Recommended |
| **2** | Fine-tuning on aerial datasets | 🔲 Future | Yes |
| **3** | Video tracking and unique vehicle counting | 🔲 Future | Yes |
| **4** | Geospatial and traffic analytics | 🔲 Future | Yes |
| **5** | Edge deployment or simulated UAV integration | 🔲 Future | Varies |

---

## Phase 1: Vehicle Detection and Image Counting (CURRENT)

- **Goal:** Detect and accurately count vehicles in static aerial or drone images.
- **Methods:** Object-detection models (YOLOv8, YOLO11, YOLOv26, RT-DETR), bounding-box processing, and OpenCV for geometry and counting.
- **Focus:** Building a robust, reproducible pipeline with standardized adapter interface, data structures, and experiment tracking.
- **Datasets:** VisDrone (primary). UAVDT converter is stubbed but not implemented.
- **Deliverables:** Inference notebooks (03–06), counting utilities, dataset converter, validation tooling.

## Phase 2: Fine-Tuning on Aerial Datasets

- **Goal:** Improve model accuracy specifically for aerial perspectives.
- **Methods:** Transfer learning and fine-tuning using VisDrone and other drone imagery datasets.
- **Prerequisite:** Phase 1 pipeline complete, validated dataset, GPU access.

## Phase 3: Video Tracking and Unique Vehicle Counting

- **Goal:** Track vehicles across video frames and count unique instances (not just per-frame detections).
- **Methods:** Multi-object tracking (MOT) algorithms, trajectory analysis.
- **Prerequisite:** Phases 1–2, video dataset, tracking library integration.

## Phase 4: Geospatial and Traffic Analytics

- **Goal:** Derive actionable insights from tracking data.
- **Methods:** Speed estimation, density maps, flow analysis, integration with geospatial coordinates.
- **Prerequisite:** Phases 1–3, geospatial tooling.

## Phase 5: Edge Deployment or Simulated UAV Integration

- **Goal:** Deploy the solution to run efficiently on edge devices or simulated drone hardware.
- **Methods:** Model optimization (TensorRT, ONNX), real-time processing pipelines.
- **Prerequisite:** Phases 1–4, edge hardware or simulator.

---

## Important Notes

- **Do not implement future-phase features** unless explicitly requested. The codebase should remain focused on the current phase.
- **Do not fabricate results** for phases that have not been executed.
- **Phase boundaries are strict** — mixing phase concerns (e.g., adding tracking code during Phase 1) creates maintenance burden and scope creep.
