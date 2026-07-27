# Instructions for Coding Agents

This repository is **AeroNetra**, a research software project. Please adhere to the following rules:

## Core Directives
- **Treat this as research software.** It is not a website, mobile application, dashboard, or API product.
- **No frontend frameworks.** Never add frontend frameworks or website code unless explicitly requested.
- **Inspect before editing.** Always inspect the repository and existing files before making changes. Preserve useful files and avoid unnecessary overwrites.
- **Small, reviewable changes.** Prefer smaller, iterative modifications.

## Code Organization
- **Reusable Logic.** Keep reusable logic (e.g., bounding-box processing, dataset loaders) in `src/aeronetra/`.
- **Notebooks.** Notebooks should call library functions from `src/aeronetra/` instead of duplicating major logic. Keep notebook cells short and ordered. Clear notebook outputs before committing.

## Data and Experiments
- **No Fabrication.** Never fabricate benchmark results, completed training runs, model accuracy, dataset paths, or successful tests.
- **Distinguish States.** Clearly distinguish between:
  - Implemented
  - Locally tested
  - Statically validated
  - Not executed (e.g., due to missing data, GPU, internet, credentials, or dependencies)
- **No Auto-Downloads.** Avoid downloading large files automatically.
- **Dataset Paths.** Require explicit configuration for dataset paths (e.g., via environment variables).
- **Random Seeds.** Use deterministic random seeds where practical.
- **Dataset Handling.** Preserve raw datasets and write conversions/outputs into `processed` directories.
- **Metadata.** Record model name, package version, weights, dataset version, image size, confidence threshold, IoU threshold, seed, device, and timing in experiment metadata.
- **Validation.** Avoid claiming a model is "best" without measured evidence from the same validation split. Validate bounding boxes and labels before training.

## Image Processing & Utilities
- **OpenCV.** Use OpenCV for image loading, bounding-box drawing, geometric filtering, region-of-interest logic, and counting utilities.

## Best Practices
- Include docstrings, type hints, validation, and useful error messages.
- Add unit and integration tests for reusable Python modules in `tests/`.
- **Secrets.** Never place Kaggle API keys or other secrets in source code. Use environment variables.
