---
description: >-
  Known technical limitations, research risks and currently incomplete modules
  in AeroNetra.
---

# Limitations

A professional research project should make its limitations easy to find. AeroNetra currently focuses on **static aerial-image detection and image-level counting**, and several later capabilities are intentionally incomplete.

## Capability boundary

```mermaid
flowchart LR
    A[Static image] --> B[Detection]
    B --> C[Filtering]
    C --> D[Image-level count]
    D --> E[Implemented scope]

    V[Video] -. future .-> T[Tracking]
    T -. future .-> U[Unique counts]
    U -. future .-> G[Geospatial analytics]
```

## Detection risks

| Limitation                | Practical impact                                  | Mitigation direction                   |
| ------------------------- | ------------------------------------------------- | -------------------------------------- |
| Tiny aerial objects       | Missed vehicles                                   | Aerial fine-tuning, resolution studies |
| Dense scenes              | Suppression/cap-related undercount                | Tune thresholds and max detections     |
| Domain shift              | Poor transfer from ground imagery                 | Validate on aerial datasets            |
| Confidence mismatch       | Unfair cross-model comparisons                    | Tune operating point per model         |
| Single-image adapter flow | No native batch/video pipeline                    | Add only when phase scope expands      |
| Architecture-specific NMS | Incorrect post-processing can remove real objects | Keep behavior model-aware              |

## Dataset risks

* raw annotations may contain malformed or boundary-crossing boxes
* class definitions differ across datasets
* tiny boxes dominate some aerial scenes
* a converter can silently change class distribution if statistics are not checked

Always run the validator before training.

## Incomplete modules

| Area                      | Current status                  |
| ------------------------- | ------------------------------- |
| UAVDT parser              | Stub / not implemented          |
| Evaluation package        | Incomplete                      |
| Generic utilities package | Minimal/incomplete              |
| Experiment configs        | Not fully populated             |
| Model-specific configs    | Not fully populated             |
| Tracking                  | Not implemented in core Phase 1 |

{% hint style="warning" %}
Do not turn planned modules into documentation claims. A documented roadmap item is not an implemented feature.
{% endhint %}

## Performance reality

Deep detectors can reduce live-camera responsiveness when inference runs on the same CPU/GPU resources as visualization or simulation. Real deployment work will need measured profiling rather than assuming notebook speed translates to a UAV pipeline.

```mermaid
flowchart TD
    A[Camera FPS] --> D{Real-time budget}
    B[Model inference latency] --> D
    C[Pre/post-processing + ROS transport] --> D
    D -->|within budget| E[Real-time candidate]
    D -->|over budget| F[Optimize / resize / accelerate / decouple]
```

## Research interpretation

Results should always be tied to the exact dataset split, model weights, thresholds, input size, device and post-processing path. Without that metadata, comparisons are descriptive rather than reproducible.
