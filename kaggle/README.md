# AeroNetra — Kaggle Notebooks

GPU-accelerated notebooks designed to run on [Kaggle](https://www.kaggle.com/) for tasks that require a GPU (training, evaluation, batch inference).

**Why Kaggle?** This project targets UAV vehicle detection with deep learning models (YOLOv8, YOLO11, RT-DETR). Training and evaluation require a GPU. Kaggle provides free GPU access (T4 x2, P100) for up to 30 hours/week.

---

## Workflow

```
Local (no GPU)                          Kaggle (GPU)
──────────────                          ────────────
                                        01 → Convert VisDrone → YOLO format
                                             Save output as Kaggle dataset
                                                    ↓
                                        02 → Train YOLOv8n, YOLO11n, RT-DETR-l
                                             Save weights as Kaggle dataset
                                                    ↓
                                        03 → Evaluate models (mAP, precision, recall)
                                        04 → Run multi-model inference comparison
                                                    ↓
Download best.pt weights ←───────────── Download from notebook output
        ↓
Use in local notebooks 03–06
(inference, counting, visualization)
```

---

## Notebooks

| # | Notebook | GPU Needed | Purpose |
|---|----------|-----------|---------|
| 01 | `01_dataset_preparation.ipynb` | No | Convert VisDrone annotations → YOLO format |
| 02 | `02_model_training.ipynb` | **Yes** | Fine-tune YOLOv8n, YOLO11n, RT-DETR-l on VisDrone |
| 03 | `03_model_evaluation.ipynb` | **Yes** | Compute mAP@50, mAP@50-95, precision, recall |
| 04 | `04_inference_comparison.ipynb` | **Yes** | Side-by-side inference with all models |

---

## Setup Instructions

### Step 1: Upload VisDrone Dataset

Add the public VisDrone dataset to Kaggle:
- Search for `shisuiotsutsuki/visdrone2019-det` on Kaggle Datasets
- Or upload your own VisDrone-DET dataset

### Step 2: Run Notebook 01 (Dataset Prep)

1. Create a new Kaggle notebook
2. Add dataset: `visdrone2019-det`
3. Upload `01_dataset_preparation.ipynb`
4. Run all cells
5. **Save the output as a new Kaggle dataset** → name it `aeronetra-visdrone-yolo`

### Step 3: Run Notebook 02 (Training)

1. Create a new Kaggle notebook
2. Add dataset: `aeronetra-visdrone-yolo` (from Step 2)
3. **Enable GPU**: Settings → Accelerator → GPU T4 x2
4. **Enable Internet**: Settings → Internet → On
5. Upload `02_model_training.ipynb`
6. Run all cells (training takes 1-3 hours total)
7. **Save output as dataset** → name it `aeronetra-trained-weights`
8. Also download `best_weights/*.pt` files to your local `outputs/models/`

### Step 4: Run Notebooks 03-04 (Evaluation & Inference)

1. Add datasets: `aeronetra-visdrone-yolo` + `aeronetra-trained-weights`
2. Enable GPU
3. Run notebooks — results saved to `/kaggle/working/`

### Step 5: Use Weights Locally

Place downloaded `.pt` files in your local project:

```
outputs/models/
├── yolov8n_visdrone_best.pt
├── yolo11n_visdrone_best.pt
└── rtdetr_l_visdrone_best.pt
```

Then use them in local notebooks (03–06):

```python
from aeronetra.detection.adapters import get_model_adapter

adapter = get_model_adapter(
    model_name="YOLOv8",
    weights_path="outputs/models/yolov8n_visdrone_best.pt",
    class_names={0: "car", 1: "van", 2: "truck", ...},
    device="cpu",
)
adapter.load_model()
prediction = adapter.predict(image, conf_thresh=0.25, iou_thresh=0.45)
```

---

## Design Decisions

- **Self-contained**: All helper code is inlined — no `pip install` of the aeronetra package required. This avoids setup failures and works offline on Kaggle.
- **Kaggle dataset chaining**: Each notebook's output can be saved as a Kaggle dataset and attached to the next notebook. This avoids re-running earlier steps.
- **Same data structures**: The inlined `BoundingBox`, `Detection`, `ModelPrediction` classes match `src/aeronetra/detection/types.py` exactly.
- **Same hyperparameters**: Confidence (0.25), IOU (0.45), image size (640) match `configs/inference/inference.yaml`.

---

## Kaggle Limits to Know

| Resource | Limit |
|----------|-------|
| GPU quota | 30 hours/week |
| Notebook timeout | 12 hours max |
| Output size | 20 GB |
| Disk space | ~70 GB total |
| Internet | Must be enabled manually for weight downloads |
