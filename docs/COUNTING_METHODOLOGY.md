---
description: >-
  How AeroNetra converts detections into image-level vehicle counts, including
  filtering logic, aerial-imagery failure modes and the distinction from
  tracking.
---

# Counting Methodology

AeroNetra's current counting method is intentionally simple: **one valid detection box in one image contributes one object to that image's count**.

{% hint style="info" %}
Image-level counting is not unique vehicle counting across time. Unique counting requires tracking and persistent identities across video frames.
{% endhint %}

## Counting pipeline

```mermaid
flowchart LR
    A[Image] --> B[Detector]
    B --> C[ModelPrediction]
    C --> D[Confidence filter]
    D --> E[Class filter]
    E --> F[Area / aspect-ratio filter]
    F --> G[ROI filter]
    G --> H{Architecture}
    H -->|YOLO| I[Optional NMS]
    H -->|RT-DETR| J[No extra YOLO-style NMS]
    I --> K[count_vehicles]
    J --> K
    K --> L[Total + per-class counts]
```

## Core functions

| Function                   | Purpose                                           |
| -------------------------- | ------------------------------------------------- |
| `count_vehicles()`         | Return total and per-class counts                 |
| `filter_by_area()`         | Remove implausibly small/large boxes              |
| `filter_by_aspect_ratio()` | Reject extreme shapes                             |
| `filter_by_roi()`          | Restrict counting to a region                     |
| `apply_nms()`              | Suppress overlapping duplicates where appropriate |

## Why a count can be wrong

```mermaid
flowchart TD
    GT[True vehicles in scene] --> FN[Missed detections]
    GT --> TP[Correct detections]
    FP[False / duplicate detections] --> OBS[Observed count]
    TP --> OBS
    FN -. lowers count .-> OBS
    FP -. raises count .-> OBS
```

Typical aerial-imagery failure modes include:

* tiny vehicles occupying very few pixels
* occlusion from trees, buildings or nearby vehicles
* dense traffic where boxes strongly overlap
* class confusion between similar vehicle types
* partial vehicles at image boundaries
* domain shift between pretraining imagery and drone viewpoints
* overly low confidence thresholds producing false positives
* overly aggressive suppression removing real neighboring vehicles

## ROI counting

A Region of Interest is useful when the question is local—for example, “how many vehicles are inside this road segment?” rather than “how many detections exist anywhere in the image?”

```mermaid
flowchart LR
    A[All detections] --> B{Center / geometry inside ROI?}
    B -->|Yes| C[Keep]
    B -->|No| D[Ignore]
    C --> E[Count]
```

## Interpreting results

A count should be reported together with the conditions that produced it: model, weights, dataset/image, thresholds, input size and filtering steps. Otherwise two numbers that look comparable may come from different pipelines.

## What Phase 3 changes

When video tracking is introduced, the logic becomes:

```mermaid
flowchart LR
    F1[Frame t] --> D1[Detections]
    F2[Frame t+1] --> D2[Detections]
    D1 --> T[Tracker]
    D2 --> T
    T --> ID[Persistent track IDs]
    ID --> U[Unique vehicle count]
```

That is fundamentally different from summing boxes frame by frame.
