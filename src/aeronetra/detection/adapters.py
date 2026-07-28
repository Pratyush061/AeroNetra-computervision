"""
Common model adapter interfaces for consistent object detection behavior.
"""
from abc import ABC, abstractmethod
from typing import Dict
import numpy as np
import time

from src.aeronetra.detection.types import BoundingBox, Detection, ModelPrediction

class BaseDetector(ABC):
    """Abstract base class for all object detectors."""
    def __init__(self, weights_path: str, class_names: Dict[int, str], device: str = "cpu"):
        self.weights_path = weights_path
        self.class_names = class_names
        self.device = device
        self.model = None

    @abstractmethod
    def load_model(self):
        """Loads the model into memory. Must be called explicitly."""
        pass

    @abstractmethod
    def predict(self, image: np.ndarray, conf_thresh: float = 0.25, iou_thresh: float = 0.45) -> ModelPrediction:
        """Runs inference on a single image and returns standardized detections."""
        pass

class UltralyticsAdapter(BaseDetector):
    """
    Adapter for Ultralytics models (YOLOv8, YOLO11, YOLO26, RT-DETR).
    Requires the ultralytics package.
    """
    def __init__(self, model_type: str, weights_path: str, class_names: Dict[int, str], device: str = "cpu"):
        super().__init__(weights_path, class_names, device)
        self.model_type = model_type

    def load_model(self):
        try:
            from ultralytics import YOLO, RTDETR
            # For RT-DETR
            if "rtdetr" in self.weights_path.lower() or self.model_type.lower() == "rtdetr":
                self.model = RTDETR(self.weights_path)
            else:
                self.model = YOLO(self.weights_path)
            self.model.to(self.device)
        except ImportError:
            raise ImportError("Please install ultralytics to use this adapter.")
        except Exception as e:
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

# Factory function
def get_model_adapter(model_name: str, weights_path: str, class_names: Dict[int, str], device: str = "cpu") -> BaseDetector:
    """Returns the appropriate adapter instance based on the model name."""
    lower_name = model_name.lower()
    if "yolo" in lower_name or "rtdetr" in lower_name:
        return UltralyticsAdapter(model_name, weights_path, class_names, device)
    else:
        raise ValueError(f"No adapter available for model: {model_name}")
