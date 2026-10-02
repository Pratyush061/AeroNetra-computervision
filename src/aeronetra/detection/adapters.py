"""Model adapter interfaces for consistent object detection behavior."""

import logging
import time
from abc import ABC, abstractmethod

import cv2
import numpy as np

from aeronetra.detection.types import BoundingBox, Detection, ModelPrediction

logger = logging.getLogger(__name__)

# Supported model name patterns for the factory function.
_ULTRALYTICS_PATTERNS = ("yolo", "rtdetr", "rt-detr")
_ONNX_PATTERNS = ("onnx",)

class BaseDetector(ABC):
    """Abstract base class for all object detectors."""
    def __init__(self, weights_path: str, class_names: dict[int, str], device: str = "cpu"):
        self.weights_path = weights_path
        self.class_names = class_names
        self.device = device
        self.model = None

    @abstractmethod
    def load_model(self):
        """Loads the model into memory. Must be called explicitly."""

    @abstractmethod
    def predict(self, image: np.ndarray, conf_thresh: float = 0.25, iou_thresh: float = 0.45) -> ModelPrediction:
        """Runs inference on a single image and returns standardized detections."""

class UltralyticsAdapter(BaseDetector):
    """
    Adapter for Ultralytics models (YOLOv8, YOLO11, YOLO26, RT-DETR).
    Requires the ultralytics package.
    """
    def __init__(self, model_type: str, weights_path: str, class_names: dict[int, str], device: str = "cpu"):
        super().__init__(weights_path, class_names, device)
        self.model_type = model_type

    def load_model(self):
        try:
            from ultralytics import RTDETR, YOLO
        except ImportError:
            raise ImportError(
                "Please install ultralytics: pip install ultralytics"
            )

        try:
            lower = self.model_type.lower().replace("-", "")
            if "rtdetr" in lower:
                self.model = RTDETR(self.weights_path)
            else:
                self.model = YOLO(self.weights_path)
            self.model.to(self.device)
            logger.info(
                "Loaded %s from %s on %s",
                self.model_type, self.weights_path, self.device,
            )
        except (AttributeError, TypeError, RuntimeError, OSError) as e:
            raise RuntimeError(f"Failed to load {self.model_type} from {self.weights_path}. Error: {e}")

    def predict(self, image: np.ndarray, conf_thresh: float = 0.25, iou_thresh: float = 0.45) -> ModelPrediction:
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        start_time = time.time()

        # RT-DETR might handle kwargs slightly differently, but standard YOLO predict works similarly for both in ultralytics.
        results = self.model.predict(
            source=image,
            conf=conf_thresh,
            iou=iou_thresh,
            device=self.device,
            verbose=False
        )

        end_time = time.time()
        inference_time_ms = (end_time - start_time) * 1000

        detections = []
        result = results[0]

        # Results object has a 'boxes' attribute
        if result.boxes is not None:
            boxes = result.boxes.xyxy.cpu().numpy()
            confs = result.boxes.conf.cpu().numpy()
            classes = result.boxes.cls.cpu().numpy()

            for box, conf, cls_id in zip(boxes, confs, classes):
                cid = int(cls_id)
                cname = self.class_names.get(cid, str(cid))

                det = Detection(
                    box=BoundingBox(xmin=float(box[0]), ymin=float(box[1]), xmax=float(box[2]), ymax=float(box[3])),
                    class_id=cid,
                    class_name=cname,
                    confidence=float(conf),
                    source_model=self.model_type
                )
                detections.append(det)

        img_h, img_w = image.shape[:2]
        return ModelPrediction(
            detections=detections,
            image_width=img_w,
            image_height=img_h,
            inference_time_ms=inference_time_ms
        )

def _letterbox(image: np.ndarray, size: tuple[int, int]) -> tuple[np.ndarray, float, int, int]:
    """Resize preserving aspect ratio and pad to ``size`` with grey (114).

    Returns the padded canvas plus the scale and the left/top padding, so
    detections can be mapped back to the original image's pixel space.
    """
    target_w, target_h = size
    height, width = image.shape[:2]
    scale = min(target_w / width, target_h / height)
    new_w, new_h = int(round(width * scale)), int(round(height * scale))
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    canvas = np.full((target_h, target_w, 3), 114, dtype=np.uint8)
    pad_x, pad_y = (target_w - new_w) // 2, (target_h - new_h) // 2
    canvas[pad_y:pad_y + new_h, pad_x:pad_x + new_w] = resized
    return canvas, scale, pad_x, pad_y

def _box_iou(a: np.ndarray, b: np.ndarray) -> float:
    """IoU of two xyxy boxes given as length-4 arrays."""
    inter_w = min(a[2], b[2]) - max(a[0], b[0])
    inter_h = min(a[3], b[3]) - max(a[1], b[1])
    if inter_w <= 0 or inter_h <= 0:
        return 0.0
    intersection = inter_w * inter_h
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - intersection
    return intersection / union if union > 0 else 0.0

def _nms(
    boxes: np.ndarray, confs: np.ndarray, classes: np.ndarray, iou_threshold: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Class-aware greedy non-maximum suppression on xyxy boxes.

    Ultralytics' default NMS is class-aware, so boxes of different classes do
    not suppress one another. O(N^2) in the number of candidate boxes, which is
    small after confidence filtering.
    """
    order = list(np.argsort(-confs))
    keep: list[int] = []
    while order:
        best = order[0]
        keep.append(best)
        order = [
            j
            for j in order[1:]
            if classes[j] != classes[best]
            or _box_iou(boxes[best], boxes[j]) <= iou_threshold
        ]
    kept = np.array(keep, dtype=int)
    return boxes[kept], confs[kept], classes[kept]

def _parse_onnx_output(
    raw: np.ndarray, conf_thresh: float, num_classes: int
) -> tuple[bool, np.ndarray, np.ndarray, np.ndarray]:
    """Normalise a detector's ONNX output into xyxy boxes, confidences, classes.

    Handles the two layouts the exported models in this project produce:

    * raw YOLO export — ``(1, 4+nc, N)`` or ``(1, N, 4+nc)``: box centre form
      ``cx, cy, w, h`` followed by per-class scores. Confidence is the maximum
      score and the class its argmax. Needs NMS afterwards.
    * end-to-end export — ``(1, N, 6)``: ``x1, y1, x2, y2, conf, class``,
      already suppressed.

    The channel count (``4 + num_classes``) is used to tell the box axis from
    the anchor axis, which is more reliable than assuming there are more anchors
    than channels. When ``num_classes`` makes the raw width 6, a 6-wide output
    is read as raw rather than end-to-end; the project does not use a 2-class
    head, so this does not arise in practice.

    Returns:
        ``(end_to_end, boxes_xyxy, confidences, class_ids)`` where
        ``end_to_end`` says whether the caller should still run NMS.
    """
    array = np.squeeze(raw, axis=0)
    if array.ndim != 2:
        raise ValueError(
            f"Unexpected ONNX output shape {raw.shape}; expected a 2D array "
            "once the batch axis is squeezed."
        )

    expected = 4 + num_classes
    if array.shape[-1] == expected:  # (N, C)
        pass
    elif array.shape[0] == expected:  # (C, N)
        array = array.T
    elif array.shape[-1] == 6:  # (N, 6) end-to-end
        keep = array[:, 4] >= conf_thresh
        return True, array[keep, :4], array[keep, 4], array[keep, 5].astype(int)
    elif array.shape[0] == 6:  # (6, N) end-to-end
        array = array.T
        keep = array[:, 4] >= conf_thresh
        return True, array[keep, :4], array[keep, 4], array[keep, 5].astype(int)
    else:
        raise ValueError(
            f"Unexpected ONNX output shape {raw.shape}; expected {expected} "
            f"channels (4 box + {num_classes} classes) or 6 (end-to-end)."
        )

    cx, cy, w, h = array[:, 0], array[:, 1], array[:, 2], array[:, 3]
    scores = array[:, 4:]
    classes = scores.argmax(axis=1)
    confs = scores[np.arange(scores.shape[0]), classes]
    keep = confs >= conf_thresh
    boxes = np.stack([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], axis=1)
    return False, boxes[keep], confs[keep], classes[keep]

class OnnxRuntimeAdapter(BaseDetector):
    """Adapter that runs a detector exported to ONNX via ONNX Runtime.

    This is a second, independent backend behind the same ``predict()``
    contract as :class:`UltralyticsAdapter`, which is what makes the pipeline's
    detector-agnostic claim real rather than aspirational: the downstream
    counting, filtering and evaluation code cannot tell the two apart. It runs
    on CPU or CUDA depending on ``device`` and needs only ``onnxruntime``.

    See :func:`_parse_onnx_output` for the supported output layouts.
    """

    def __init__(
        self,
        model_type: str,
        weights_path: str,
        class_names: dict[int, str],
        device: str = "cpu",
        input_size: tuple[int, int] = (640, 640),
    ):
        super().__init__(weights_path, class_names, device)
        self.model_type = model_type
        self.input_size = (int(input_size[0]), int(input_size[1]))
        self.session = None
        self.input_name: str | None = None

    def load_model(self):
        try:
            import onnxruntime as ort
        except ImportError:
            raise ImportError(
                "Please install onnxruntime: pip install onnxruntime"
            )

        providers = (
            ["CUDAExecutionProvider", "CPUExecutionProvider"]
            if "cuda" in self.device.lower()
            else ["CPUExecutionProvider"]
        )
        try:
            self.session = ort.InferenceSession(self.weights_path, providers=providers)
        except (ValueError, RuntimeError, OSError) as e:
            raise RuntimeError(
                f"Failed to load ONNX model {self.weights_path}. Error: {e}"
            )
        self.input_name = self.session.get_inputs()[0].name
        logger.info(
            "Loaded ONNX model %s from %s on %s",
            self.model_type, self.weights_path, self.device,
        )

    def predict(self, image: np.ndarray, conf_thresh: float = 0.25, iou_thresh: float = 0.45) -> ModelPrediction:
        if self.session is None or self.input_name is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        start_time = time.time()

        canvas, scale, pad_x, pad_y = _letterbox(image, self.input_size)
        # BGR uint8 image -> RGB, NCHW, float32 in [0, 1].
        blob = canvas[:, :, ::-1].transpose(2, 0, 1)[np.newaxis].astype(np.float32) / 255.0
        raw = self.session.run(None, {self.input_name: blob})[0]

        end_to_end, boxes, confs, classes = _parse_onnx_output(
            raw, conf_thresh, len(self.class_names)
        )
        if not end_to_end:
            boxes, confs, classes = _nms(boxes, confs, classes, iou_thresh)

        img_h, img_w = image.shape[:2]
        detections = []
        for box, conf, cls_id in zip(boxes, confs, classes):
            xmin = min(max((box[0] - pad_x) / scale, 0.0), float(img_w))
            ymin = min(max((box[1] - pad_y) / scale, 0.0), float(img_h))
            xmax = min(max((box[2] - pad_x) / scale, 0.0), float(img_w))
            ymax = min(max((box[3] - pad_y) / scale, 0.0), float(img_h))
            if xmax <= xmin or ymax <= ymin:
                continue
            cid = int(cls_id)
            detections.append(
                Detection(
                    box=BoundingBox(xmin, ymin, xmax, ymax),
                    class_id=cid,
                    class_name=self.class_names.get(cid, str(cid)),
                    confidence=float(conf),
                    source_model=self.model_type,
                )
            )

        return ModelPrediction(
            detections=detections,
            image_width=img_w,
            image_height=img_h,
            inference_time_ms=(time.time() - start_time) * 1000,
        )

# Factory function
def get_model_adapter(
    model_name: str,
    weights_path: str,
    class_names: dict[int, str],
    device: str = "cpu",
) -> BaseDetector:
    """Returns the appropriate adapter instance based on the model name.

    Supported model names (case-insensitive):
        YOLOv8, YOLO11, YOLO26, RT-DETR, RTDETR  -> UltralyticsAdapter
        any name containing "onnx"               -> OnnxRuntimeAdapter

    A name containing both (e.g. "yolov8n.onnx") selects the ONNX backend,
    because that is the runtime the weights actually require.

    Raises:
        ValueError: If no adapter is available for the given model name.
    """
    lower_name = model_name.lower().replace("-", "")
    if any(pattern in lower_name for pattern in _ONNX_PATTERNS):
        return OnnxRuntimeAdapter(model_name, weights_path, class_names, device)
    if any(pattern.replace("-", "") in lower_name for pattern in _ULTRALYTICS_PATTERNS):
        return UltralyticsAdapter(model_name, weights_path, class_names, device)
    raise ValueError(
        f"No adapter available for model: {model_name!r}. "
        f"Supported patterns: {', '.join(_ULTRALYTICS_PATTERNS + _ONNX_PATTERNS)}"
    )
