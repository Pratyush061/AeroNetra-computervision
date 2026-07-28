# Datasets Guide

This document outlines the usage, structure, and class mappings for datasets within the AeroNetra project.

---

## Dataset Selection

We prioritize datasets in the following order:
1. **VisDrone** — Primary dataset for aerial vehicle detection (many small objects, dense scenes). **Implemented.**
2. **UAVDT** — Secondary drone traffic dataset, focus on tracking and detection. **NOT implemented** (`src/aeronetra/datasets/uavdt.py` is a stub that raises `NotImplementedError`).
3. **UA-DETRAC** — Optional fixed-camera dataset for domain comparison. **NOT implemented.**
4. **SampleDataset** — Small or generated fixtures for local testing only (in `tests/fixtures/`).

Prefer official sources over unofficial Kaggle mirrors. Always verify the license and contents if using Kaggle.

---

## Directory Structure

```
data/
├── raw/          ← Original, unmodified datasets (NEVER modify)
├── interim/      ← Intermediate transformed data
├── processed/    ← Final data ready for modeling (YOLO format output)
└── samples/      ← Small sample subsets for quick testing
```

All directories under `data/` are gitignored. Configure the dataset root via the `DATASET_DIR` environment variable, or let the code fall back to `data/raw/`.

---

## VisDrone (Primary — Implemented)

### Expected Folder Layout

```
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

### VisDrone Class IDs and Vehicle Mapping

The converter is in `src/aeronetra/datasets/visdrone.py`.

| VisDrone ID | Category | Vehicle? | Notes |
|:-----------:|----------|:--------:|-------|
| 0 | ignored region | ❌ | Skipped during conversion |
| 1 | pedestrian | ❌ | Skipped |
| 2 | people | ❌ | Skipped |
| 3 | bicycle | ✅ | Included |
| 4 | car | ✅ | Included |
| 5 | van | ✅ | Included |
| 6 | truck | ✅ | Included |
| 7 | tricycle | ✅ | Included |
| 8 | awning-tricycle | ✅ | Included |
| 9 | bus | ✅ | Included |
| 10 | motor | ✅ | Included |
| 11 | others | ❌ | Skipped |

### Conversion Modes

Two modes are supported by the converter:

- **`"merged"`** — All vehicle classes (3–10) mapped to a single class `0` ("vehicle"). Use for binary vehicle/non-vehicle detection.
- **`"separate"`** — Vehicle classes remapped sequentially starting from `0` (bicycle=0, car=1, van=2, …). Use for per-class vehicle counting.

### Key Converter Functions

| Function | Purpose |
|----------|---------|
| `parse_visdrone_row(line)` | Parses a single VisDrone annotation line |
| `map_category(visdrone_class_id, mode)` | Maps VisDrone ID to YOLO class ID (returns `None` for non-vehicle) |
| `convert_to_yolo_format(annotations, img_w, img_h, mode)` | Converts annotations to normalized YOLO format with boundary clipping |
| `convert_dataset(source_dir, output_dir, mode)` | Batch converts a full split; **returns a statistics dict** — always capture and log it |

### Dataset YAML Configs

Located in `configs/datasets/`:

| File | Description |
|------|-------------|
| `visdrone_merged.yaml` | Merged mode config — all vehicles as class 0 |
| `visdrone_separate.yaml` | Separate mode config — per-vehicle-type classes |
| `visdrone_original.yaml` | Original VisDrone class mapping |
| `visdrone_yolo.yaml` | YOLO-format dataset paths |
| `datasets.yaml` | Master dataset metadata file |

Configs use `${DATASET_DIR}` variable substitution for dataset paths.

---

## UAVDT — NOT Implemented

`src/aeronetra/datasets/uavdt.py` is a **stub that raises `NotImplementedError`**. Do not fabricate UAVDT support or claim it works. UAVDT annotations use a different format than VisDrone and would need a dedicated parser.

---

## Kaggle Setup (for downloading VisDrone)

1. Install Kaggle CLI: `pip install kaggle`
2. Obtain `kaggle.json` from your Kaggle account settings.
3. Place `kaggle.json` in `~/.kaggle/` (Linux/Mac) or `C:\Users\<username>\.kaggle\` (Windows).
4. On Linux/Mac: `chmod 600 ~/.kaggle/kaggle.json`
5. Download using the script (**requires explicit `--download` flag**):
   ```bash
   python scripts/download_dataset.py --download
   ```

---

## Dataset Validation

Before training, validate your converted dataset with:

```bash
python scripts/validate_dataset.py --dataset-dir <path> --num-classes <n>
```

The validator checks for:
- Missing image-label pairs
- Unreadable images
- Malformed label rows
- Zero-area or negative-dimension bounding boxes
- Out-of-bounds coordinates
- Invalid class IDs
- Duplicate annotation rows
- Tiny boxes (few pixels)
- Extreme aspect ratios

Returns a JSON report with class distribution and issue counts.

---

## Common Annotation Problems

| Problem | Description |
|---------|-------------|
| Out-of-bounds boxes | Coordinates exceed image dimensions — clipped during conversion |
| Zero-area boxes | Width or height is zero — filtered out during conversion |
| Ignored regions (class 0, 11) | Not vehicle targets — skipped by the converter |
| Tiny objects | VisDrone vehicles can be extremely small (few pixels) — hard to detect |

---

## Adding Another Dataset

1. Inspect the dataset format and write a dedicated converter in `src/aeronetra/datasets/`.
2. Add a new configuration file in `configs/datasets/`.
3. Document the expected folder layout and class mappings in this file.
4. Update `configs/datasets/datasets.yaml` to include the new dataset's metadata.
5. Add tests in `tests/` for the new converter.

---

## Handling Rules

- ❌ Do not commit datasets to version control.
- ❌ Never automatically download large datasets in scripts or notebooks.
- ❌ Never modify files in `data/raw/` — write conversions to `data/processed/`.
- ✅ Configure dataset paths via `DATASET_DIR` environment variable.
- ✅ Use `aeronetra.config.get_data_dir()` to resolve paths — never hardcode.
