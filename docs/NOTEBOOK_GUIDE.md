# Notebook Guide

Notebooks in this repository are for exploration, experimentation, and presenting findings. They follow a numbered progression from environment verification to model evaluation.

---

## Notebook Progression

| # | Notebook | Purpose | GPU Required |
|---|----------|---------|:------------:|
| 00 | `00_environment_check.ipynb` | Verify Python, packages, and CUDA availability | No |
| 01 | `01_dataset_exploration.ipynb` | Explore VisDrone dataset structure, class distributions, and sample images | No |
| 02 | `02_opencv_vehicle_counting.ipynb` | Traditional OpenCV-based vehicle counting (no deep learning) | No |
| 03 | `03_yolo26_inference.ipynb` | YOLOv26 inference on aerial images | Recommended |
| 04 | `04_yolo11_inference.ipynb` | YOLO11 inference on aerial images | Recommended |
| 05 | `05_yolov8_inference.ipynb` | YOLOv8 inference on aerial images | Recommended |
| 06 | `06_rtdetr_inference.ipynb` | RT-DETR inference on aerial images | Recommended |
| 07 | `07_model_training.ipynb` | Fine-tuning models on VisDrone dataset | Yes |
| 08 | `08_model_evaluation.ipynb` | Compare model performance on validation split | Recommended |

Notebooks 03–06 are **independent** — each handles a single model architecture. Weights must be loaded explicitly; models should never be silently substituted.

---

## Conventions

### Call Library Functions — Don't Duplicate

```python
# CORRECT — use library functions
from aeronetra.detection.adapters import get_model_adapter
from aeronetra.counting.ops import count_vehicles, filter_by_area

adapter = get_model_adapter("YOLOv8", weights_path, class_names, device)
adapter.load_model()
prediction = adapter.predict(image)
total, by_class = count_vehicles(prediction.detections)
```

```python
# INCORRECT — duplicating logic in notebook
def my_count_vehicles(boxes):  # Don't do this
    ...
```

### Cell Organization
- Keep cells **short and logically ordered** — one task per cell.
- Add markdown cells to explain what each section does.
- Use cells for: setup/imports → data loading → inference → post-processing → visualization.

### No Auto-Downloads
- Never auto-download model weights or datasets in notebook cells.
- Missing weights should cause a clear error, not a silent download.
- Use `scripts/download_dataset.py --download` for dataset acquisition.

### Clear Outputs Before Committing
```bash
jupyter nbconvert --clear-output --inplace notebooks/*.ipynb
```

Committed notebook outputs bloat the repository and cause noisy git diffs. Always clear before committing.

---

## Adding a New Notebook

1. Follow the numbering convention: `NN_descriptive_name.ipynb`.
2. Import from `src/aeronetra/` — do not reimplement existing functions.
3. Use `InferenceMetadata` for any inference runs (see [EXPERIMENT_GUIDE.md](EXPERIMENT_GUIDE.md)).
4. Add a markdown header cell describing the notebook's purpose.
5. Clear outputs before committing.
