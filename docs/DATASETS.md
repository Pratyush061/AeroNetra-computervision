# Datasets Guide

This document outlines the usage and structure for datasets within the AeroNetra project.

## Dataset Selection
We prioritize datasets in the following order:
1. **VisDrone**: Primary dataset for aerial vehicle detection (many small objects, dense scenes).
2. **UAVDT**: Secondary drone traffic dataset, focus on tracking and detection.
3. **UA-DETRAC**: Optional fixed-camera dataset for domain comparison.
4. **SampleDataset**: Very small or generated fixtures for local testing only.

Prefer official sources over unofficial Kaggle mirrors. Always verify the license and contents if using Kaggle.

## Directory Structure
- `data/raw/`: Original, unmodified datasets.
- `data/interim/`: Intermediate data that has been transformed.
- `data/processed/`: Final, processed data ready for modeling.
- `data/samples/`: Small sample subsets for quick testing and debugging.

## Expected Folder Layouts (e.g., VisDrone)
```text
data/raw/VisDrone2019/
├── VisDrone2019-DET-train/
│   ├── images/
│   └── annotations/
├── VisDrone2019-DET-val/
│   ├── images/
│   └── annotations/
└── VisDrone2019-DET-test-dev/
    ├── images/
    └── annotations/
```

## Kaggle Setup
To download datasets using Kaggle:
1. Ensure the Kaggle CLI is installed (`pip install kaggle`).
2. Obtain your `kaggle.json` credentials from your Kaggle account settings.
3. Place `kaggle.json` in `~/.kaggle/` and run `chmod 600 ~/.kaggle/kaggle.json`.
4. Use the provided dataset download script with the `--download` flag.

## Class Mappings
VisDrone has several classes. For our vehicle detection focus, we map the following classes:
- 3: car
- 4: van
- 5: truck
- 6: tricycle
- 7: awning-tricycle
- 8: bus
- 9: motor

We support two modes:
- **Merged**: All vehicle classes mapped to class ID `0` (`vehicle`).
- **Separate**: Classes are mapped sequentially starting from `0`.

## Common Annotation Problems
- Out-of-bounds boxes.
- Zero-area or negative-dimension boxes.
- Ignored regions (class 0 or 11 in VisDrone) that should not be converted as targets.

## Dataset Limitations
- VisDrone objects are often extremely small.
- UAVDT annotations use a different format than VisDrone.
- UA-DETRAC has a domain gap (ground-level perspective).

## Adding Another Dataset
1. Inspect the dataset format and write a dedicated converter in `src/aeronetra/datasets/`.
2. Add a new configuration file in `configs/datasets/`.
3. Document the expected folder layout and class mappings in this file.
4. Update `configs/datasets/datasets.yaml` to include the new dataset's metadata.

## Handling Rules
- Do not commit datasets to version control.
- Ensure datasets are handled properly and configured via environment variables (e.g., `DATASET_DIR`).
- Never automatically download large datasets in scripts or notebooks.
- Preserve raw datasets and write conversions/outputs into `processed` directories.
