---
description: >-
  A phased roadmap from static aerial detection to tracking, traffic analytics
  and UAV/edge integration.
---

# Research Scope

AeroNetra is intentionally phased. Each stage should create a reliable foundation for the next rather than combining detection, tracking, mapping and deployment before the earlier layers are measurable.

## Roadmap

```mermaid
flowchart LR
    P1[Phase 1<br/>Static Detection & Counting] --> P2[Phase 2<br/>Aerial Fine-tuning]
    P2 --> P3[Phase 3<br/>Video Tracking & Unique Counts]
    P3 --> P4[Phase 4<br/>Traffic + Geospatial Analytics]
    P4 --> P5[Phase 5<br/>Edge / Simulated UAV Integration]
```

| Phase | Primary question                                                       | Status     |
| ----- | ---------------------------------------------------------------------- | ---------- |
| **1** | Can we detect and count vehicles reliably in individual aerial images? | 🟢 Current |
| **2** | Can aerial fine-tuning improve detection quality?                      | Planned    |
| **3** | Can vehicles retain identities across frames?                          | Planned    |
| **4** | Can tracks become useful traffic/geospatial signals?                   | Planned    |
| **5** | Can the pipeline operate efficiently in a UAV or simulation loop?      | Planned    |

## Phase 1 — Detection and image counting

Build the reusable research foundation:

* standardized detector adapter
* validated prediction data structures
* VisDrone conversion and validation
* filtering, ROI and counting utilities
* model-comparison workflow
* reproducible experiment metadata

**Success means:** the same image and configuration can be rerun and interpreted consistently.

## Phase 2 — Aerial fine-tuning

Use aerial datasets to improve performance on small objects, top-down viewpoints and dense traffic. Training belongs on GPU-capable infrastructure such as Kaggle when local hardware is insufficient.

## Phase 3 — Video tracking

```mermaid
flowchart LR
    A[Detector per frame] --> B[Association]
    B --> C[Persistent Track IDs]
    C --> D[Trajectory History]
    D --> E[Unique Vehicle Counts]
```

This phase changes the meaning of “count”: persistent identity replaces independent boxes.

## Phase 4 — Analytics

Potential outputs include traffic density, directional flow, trajectory statistics and eventually geospatially grounded measurements. These require calibrated assumptions and should not be inferred from raw bounding boxes alone.

## Phase 5 — UAV / edge integration

The long-term integration layer can connect perception to simulated or real UAV systems, with attention to model optimization, real-time latency, ROS 2 messaging and flight-stack boundaries.

```mermaid
flowchart LR
    CAM[Camera] --> CV[AeroNetra Perception]
    CV --> ROS[ROS 2 Interface]
    ROS --> FC[PX4 / Flight Stack]
    FC --> SIM[Gazebo / UAV]
    SIM --> CAM
```

{% hint style="warning" %}
This diagram describes the intended integration direction. It does not mean the later phases are already implemented in the core computer-vision package.
{% endhint %}
