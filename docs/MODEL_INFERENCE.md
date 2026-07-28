# Model Inference Guide

This document describes how object detection inference is structured and executed in the AeroNetra project.

## The Model Adapter Interface
To maintain a clean and consistent pipeline, all object detectors interact through a common adapter interface defined in `src/aeronetra/detection/adapters.py`.

### `BaseDetector`
This abstract class enforces two main methods:
- `load_model()`: Explicitly loads weights into memory and moves the model to the target device (CPU/GPU).
- `predict(image, conf_thresh, iou_thresh)`: Runs inference on a single image and returns a standardized `ModelPrediction` object containing a list of `Detection` instances.

### Standardized Outputs
Regardless of whether you use YOLOv8, RT-DETR, or a future custom model, the adapter normalizes outputs into the `Detection` dataclass:
- `box`: BoundingBox in xyxy format
- `class_id`: Integer class ID
- `class_name`: String class name
- `confidence`: Float confidence score

## Usage Flow
1. **Initialize Adapter**: `adapter = get_model_adapter("YOLOv8", weights_path, class_names, device)`
2. **Load Model**: `adapter.load_model()` (Avoid putting this in loops)
3. **Inference**: `prediction = adapter.predict(image_array, conf_thresh=0.25)`
4. **Filtering**: `prediction.filter_by_class([2, 5, 7])`
5. **Counting/Drawing**: Pass `prediction.detections` to functions in `src/aeronetra/counting/ops.py` and `drawing.py`.

## Avoiding Automatic Downloads
By design, notebooks and scripts do not automatically download large weights unless explicitly requested by running the respective cells.
