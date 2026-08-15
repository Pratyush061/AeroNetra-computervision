"""Model adapter interfaces for consistent object detection behavior."""

from abc import ABC, abstractmethod

import logging
import time

import numpy as np

from aeronetra.detection.types import BoundingBox, Detection, ModelPrediction

logger = logging.getLogger(__name__)

# Supported model name patterns for the factory function.
_ULTRALYTICS_PATTERNS = ("yolo", "rtdetr", "rt-detr")


class BaseDetector(ABC):
    """Abstract base class for all object detectors."""

    def __init__(
        self, weights_path: str, class_names: dict[int, str], device: str = "cpu"
    ):
        self.weights_path = weights_path
        self.class_names = class_names
        self.device = device
        self.model = None

    @abstractmethod
    def load_model(self):
        """Loads the model into memory. Must be called explicitly."""
        pass

    @abstractmethod
    def predict(
        self, image: np.ndarray, conf_thresh: float = 0.25, iou_thresh: float = 0.45
    ) -> ModelPrediction:
        """Runs inference on a single image and returns standardized detections."""
        pass


class UltralyticsAdapter(BaseDetector):
    """
    Adapter for Ultralytics models (YOLOv8, YOLO11, YOLO26, RT-DETR).
    Requires the ultralytics package.
    """

    def __init__(
        self,
        model_type: str,
        weights_path: str,
        class_names: dict[int, str],
        device: str = "cpu",
    ):
        super().__init__(weights_path, class_names, device)
        self.model_type = model_type

    def load_model(self):
        try:
            from ultralytics import YOLO, RTDETR
        except ImportError:
            raise ImportError("Please install ultralytics: pip install ultralytics")

        try:
            lower = self.model_type.lower().replace("-", "")
            if "rtdetr" in lower:
                self.model = RTDETR(self.weights_path)
            else:
                self.model = YOLO(self.weights_path)
            self.model.to(self.device)
            logger.info(
                "Loaded %s from %s on %s",
                self.model_type,
                self.weights_path,
                self.device,
            )
        except (AttributeError, TypeError, RuntimeError, OSError) as e:
            raise RuntimeError(
                f"Failed to load {self.model_type} from {self.weights_path}. Error: {e}"
            )

    def predict(
        self, image: np.ndarray, conf_thresh: float = 0.25, iou_thresh: float = 0.45
    ) -> ModelPrediction:
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        start_time = time.time()

        # RT-DETR might handle kwargs slightly differently, but standard YOLO predict works similarly for both in ultralytics.
        results = self.model.predict(
            source=image,
            conf=conf_thresh,
            iou=iou_thresh,
            device=self.device,
            verbose=False,
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
                    box=BoundingBox(
                        xmin=float(box[0]),
                        ymin=float(box[1]),
                        xmax=float(box[2]),
                        ymax=float(box[3]),
                    ),
                    class_id=cid,
                    class_name=cname,
                    confidence=float(conf),
                    source_model=self.model_type,
                )
                detections.append(det)

        img_h, img_w = image.shape[:2]
        return ModelPrediction(
            detections=detections,
            image_width=img_w,
            image_height=img_h,
            inference_time_ms=inference_time_ms,
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
        YOLOv8, YOLO11, YOLOv26, RT-DETR, RTDETR

    Raises:
        ValueError: If no adapter is available for the given model name.
    """
    lower_name = model_name.lower().replace("-", "")
    if any(pattern.replace("-", "") in lower_name for pattern in _ULTRALYTICS_PATTERNS):
        return UltralyticsAdapter(model_name, weights_path, class_names, device)
    raise ValueError(
        f"No adapter available for model: {model_name!r}. "
        f"Supported patterns: {', '.join(_ULTRALYTICS_PATTERNS)}"
    )
