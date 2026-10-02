---
description: >-
  How work is chosen, sequenced and verified in AeroNetra, plus the current
  research direction and the decisions already taken.
---

# Research Process

This document exists so a new contributor — human or an AI agent — can pick up the project without re-litigating decisions that have already been made. It records *how* work is chosen and verified. The *what* (the phased roadmap) lives in [Research Scope](RESEARCH_SCOPE.md).

## How work is chosen

* Work follows the [phased roadmap](RESEARCH_SCOPE.md). Later phases build on measurable earlier ones, so a later capability is never presented as already implemented.
* One step at a time, in small reviewable changes. Prefer an iterative modification over a large rewrite.
* When a decision has meaningful trade-offs, it is raised with concrete options rather than guessed at.
* Claims are verified — against a source, or by running the code — instead of being recalled. A short run beats a confident guess.

## Evidence rules

* Never fabricate results, metrics, test status or dataset paths.
* Distinguish four states explicitly: **implemented and tested**, **implemented but untested**, **stub**, and **not executed**.
* A number is only a result if it was measured on the data and settings recorded alongside it.
* Robustness claims may only be made against **real** data (see below).

## Current direction (Phase 2): robustness across conditions

The research question is not "how high can we push VisDrone accuracy" but whether the detector keeps working under conditions it was **not** trained on: illumination, weather, altitude, viewpoint, density and occlusion. VisDrone and UAVDT are largely clear, daytime, mid-altitude footage, which is not what a UAV actually meets.

The ordering is deliberate — **measure before improving**:

1. **Measurement layer.** Stratified evaluation is implemented and tested: `evaluate_by_stratum()` reports precision/recall/F1 per object-size and image-density band, and `evaluate_all(..., include_strata=True)` folds it into the JSON report. See [Evaluation Guide](EVALUATION.md).
2. **Condition-labelled data.** Next: an adapter for a dataset that actually contains adverse conditions, so the weather/night axis can be measured rather than assumed.
3. **Robustness training under an edge budget.** After that: augmentation and domain-generalisation work on a small model, reported per condition.

You cannot improve what you cannot measure, and you cannot claim robustness on data that does not contain the condition.

## Synthetic and augmented data

Augmentation and simulation are a **training** axis and a cheap way to sweep conditions. They are not evidence:

* Synthetic weather degrades a clear image; it cannot create the semantic change that matters most (snow-covered vehicles on snow-covered roads).
* Fine-tuning plus augmentation alone has been shown not to solve this.

All robustness claims are therefore made on real adverse-weather data.

## Candidate datasets for adverse conditions

Not adopted yet — candidates only. Licensing and availability must be checked before use, and datasets and weights are staged manually (never auto-downloaded).

| Dataset | Conditions | Notes |
| --- | --- | --- |
| Nordic Vehicle Dataset (NVD) | Real UAV imagery in snow, overcast and low light | Closest match to the snow case |
| SWUAV | 12 adverse weather/illumination conditions, including blizzard, dense fog, heavy rain and backlit night | Larger, explicitly built for robustness and generalisation |
| DroneVehicle | Day, night and dark-night | RGB + infrared; annotated with **oriented** boxes, so an OBB → axis-aligned step is needed |

## Edge budget

The edge budget is deliberately **not fixed yet**, so robustness can be studied first. It must stay re-tightenable: the evaluation and adapter layers are kept model-agnostic so a small model can be swapped in later without reworking them. The working assumption is a small detector class (order of ten million parameters), to be measured when the budget is set.

## Decisions already taken (do not re-litigate)

* **Grounding DINO** is parked as a Phase-2 *candidate* for open-vocabulary detection, not adopted. Zero-shot open-vocabulary detection transfers poorly to aerial drone imagery (the Grounding DINO 1.5 paper reports roughly 13 AP on the ODinW `AerialDrone` set), so it is not a free win. If pursued it needs a new adapter behind `get_model_adapter()`, a prompt field in `InferenceMetadata`, and manually staged weights.
* **Stratified evaluation covers size and density only** for now. Occlusion and truncation need per-object attributes, which `GroundTruthObject` does not carry yet.
* **Evaluation is class-aware only.** `evaluate_detection()` and `evaluate_by_stratum()` both reject class-agnostic aggregation, because the report schema is class-based and class-agnostic matching would break the reconciliation between strata and aggregate metrics.
* **Synthetic data is not evidence** (see above).
* **The ROS 2 / Gazebo harness is the only documented exception** to the model-adapter rule; it is a narrow, tested integration and must not be copied into reusable library code.

## Open follow-ups

* Occlusion/truncation strata — extend `GroundTruthObject` and the VisDrone loader.
* A loader-level guard for prediction / ground-truth image-id mismatches.
* Consolidate the two matching passes in the evaluation package (`evaluate_detection` and `evaluate_by_stratum` currently match independently).
* UAVDT: an optional `include_empty_frames` mode.
* Land one adverse-weather dataset adapter at a time.
* Define the edge budget.

## How changes land

* A branch and pull request is the default. The maintainer may direct documentation or follow-up changes straight to `main`.
* Keep model-specific logic inside adapters; notebooks call the library rather than duplicating it.
* Run `ruff check .` and `pytest` before landing, and record experiment metadata with every result.
