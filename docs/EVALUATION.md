---
description: >-
  How AeroNetra turns predictions and ground truth into detection and
  counting metrics, and how to record a reproducible evaluation report.
---

# Evaluation Guide

AeroNetra's evaluation package (`src/aeronetra/evaluation/`) closes the Phase 1 model-comparison loop: it converts standardised `ModelPrediction` objects and a ground-truth set into the exact metrics promised by [Model Comparison](MODEL_COMPARISON.md) and the [Experiment Guide](EXPERIMENT_GUIDE.md).

{% hint style="info" %}
Ground truth is a separate type from a detection. A `GroundTruthObject` carries only a class id and an absolute `xyxy` box — no confidence and no model provenance — so predictions and annotations can never be confused.
{% endhint %}

## Pipeline

```mermaid
flowchart LR
    P[ModelPrediction per image] --> C[Confidence filter]
    G[GroundTruth per image] --> M[IoU matching]
    C --> M
    M --> D[Precision / Recall / F1]
    M --> A[mAP@50 / mAP@50-95]
    C --> N[Count per image]
    G --> E[Actual count per image]
    N --> K[Count error: MAE / RMSE / bias / MAPE]
    E --> K
    D --> R[EvaluationReport]
    A --> R
    K --> R
    R --> J[JSON export]
```

## What each module does

| Module                    | Responsibility                                                        |
| ------------------------- | --------------------------------------------------------------------- |
| `evaluation/matching.py`  | `iou()` and greedy, class-aware `match_image()`                       |
| `evaluation/detection.py` | `evaluate_detection()` — precision/recall/F1 and mAP@50 / mAP@50-95   |
| `evaluation/counting.py`  | `evaluate_counting()` — MAE, RMSE, bias, MAPE against true counts     |
| `evaluation/groundtruth.py` | `load_yolo_ground_truth()`, `load_visdrone_ground_truth()`          |
| `evaluation/strata.py`    | `evaluate_by_stratum()` — metrics per object-size and density band    |
| `evaluation/report.py`    | `evaluate_all()` and `save_report()` — one combined JSON report       |
| `evaluation/types.py`     | Ground-truth and metric data structures                               |

## Detection metrics

Matching follows the VOC/COCO rule: detections are taken highest-confidence first and each is paired with the best-IoU unmatched ground truth **of the same class** that clears the IoU threshold. Unpaired detections are false positives; unpaired annotations are false negatives.

{% hint style="info" %}
Two confidence thresholds are used deliberately. `ap_conf_threshold` (default `0.001`) builds the precision/recall curve, so mAP is not truncated by the operating point. `conf_threshold` (default `0.25`) defines the operating point reported as precision/recall/F1 and is the threshold counting uses.
{% endhint %}

* **Precision / Recall / F1** are micro-averaged across classes at a single operating IoU (`0.5`), after the operating-point confidence threshold is applied.
* **AP@50** is the 101-point interpolated average precision at IoU 0.5.
* **mAP@50** and **mAP@50-95** average AP over classes that have ground truth; classes that appear only in predictions are reported per-class but excluded from the mean.
* **Inference latency** is averaged from each prediction's `inference_time_ms`.

## Stratified detection metrics

Aggregate precision and recall hide *where* a model fails. `evaluate_by_stratum()` re-uses the same matching and the same operating point as `evaluate_detection()`, and reports precision, recall and F1 per stratum:

* **Object size** — absolute pixel area, following COCO's convention (`small` below 32², `medium` below 96², `large` otherwise). A matched pair is attributed to the ground-truth box; a false positive to the detection box.
* **Image density** — annotated objects per image (`sparse` up to 10, `moderate` up to 50, `dense` up to 100, `very_dense` above). Each image contributes all of its true positives, false positives and false negatives to one band.

Both sets of bounds are parameters, and every configured band is always present, so a band with no objects is reported with zero support rather than omitted. Because the strata come from the same matching pass, their counts reconcile with the aggregate metrics.

{% hint style="info" %}
Only strata derivable from boxes are computed here. Occlusion and truncation need per-object attributes, which `GroundTruthObject` does not carry yet — that is the next extension.
{% endhint %}

## Counting metrics

Image-level counting compares predicted counts against annotated counts. Images present on only one side are treated as a count of zero on the missing side, so a missed or spurious image is a real error rather than a silently dropped row. `predicted_counts()` accepts an optional `class_ids` filter. When a class filter is supplied through `evaluate_all(count_class_ids=...)`, the same filter is applied to ground-truth counts so both sides use the same object subset.

| Metric | Meaning                                              |
| ------ | ---------------------------------------------------- |
| MAE    | Mean absolute error in vehicles per image            |
| RMSE   | Root-mean-square error (penalises large misses)      |
| Bias   | Mean signed error; positive means over-counting      |
| MAPE   | Mean absolute percentage error over non-zero counts  |

## Ground-truth scope

The YOLO loader follows the dataset convention that an image with no objects may have no label file, so missing YOLO label files are treated as having no ground-truth objects when they are outside the loader's file set. For VisDrone, `load_visdrone_ground_truth()` is a vehicle-only normalization helper; it is **not** a drop-in replacement for the official VisDrone challenge evaluator. The official toolkit additionally models ignored ground-truth regions and ground-truth rows with score `0` as ignored, so use the official toolkit when challenge-comparable VisDrone scores are required.

## Usage

```python
from aeronetra.evaluation import (
    evaluate_all,
    image_sizes_from_dir,
    load_yolo_ground_truth,
    save_report,
)

ground_truth = load_yolo_ground_truth(
    labels_dir,
    image_sizes_from_dir(images_dir),
)
report = evaluate_all(predictions, ground_truth, metadata=metadata)
save_report(report, outputs_dir / "metrics" / "yolov8_val.json")
```

`predictions` is a `{image_id: ModelPrediction}` mapping produced by a detector adapter. Pass the same confidence threshold that the run used; the report records both the operating-point and AP thresholds.

## Rules

* Do not fabricate metric values. Record only measured numbers, and mark unexecuted runs clearly.
* Compare models on the same validation split and the same input-size policy.
* Do not average mAP over classes with no ground truth.
* Do not apply YOLO-style NMS to RT-DETR output before evaluating.
* Store the `InferenceMetadata` with every report; a metric without its dataset, weights, thresholds and device is not reproducible.
* Treat this package as the project's reproducible metric layer, not as a substitute for dataset-specific official benchmark toolkits.
