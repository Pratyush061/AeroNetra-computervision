"""Drawing utilities for detections, ROI overlays, and result export."""

from pathlib import Path

import csv
import cv2
import json
import numpy as np

from aeronetra.detection.types import CountSummary, Detection


def draw_detections(
    image: np.ndarray,
    detections: list[Detection],
    color: tuple[int, int, int] = (0, 255, 0),
    thickness: int = 2,
) -> np.ndarray:
    """Draws bounding boxes and labels on an image."""
    out_img = image.copy()

    for d in detections:
        x1, y1 = int(d.box.xmin), int(d.box.ymin)
        x2, y2 = int(d.box.xmax), int(d.box.ymax)

        cv2.rectangle(out_img, (x1, y1), (x2, y2), color, thickness)

        label = f"{d.class_name} {d.confidence:.2f}"
        (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)

        cv2.rectangle(out_img, (x1, y1 - h - 4), (x1 + w, y1), color, -1)
        cv2.putText(
            out_img, label, (x1, y1 - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1
        )

    return out_img


def draw_roi(
    image: np.ndarray,
    roi_xyxy: tuple[float, float, float, float],
    color: tuple[int, int, int] = (0, 0, 255),
    thickness: int = 2,
) -> np.ndarray:
    """Draws a Region of Interest rectangle."""
    out_img = image.copy()
    x1, y1, x2, y2 = map(int, roi_xyxy)
    cv2.rectangle(out_img, (x1, y1), (x2, y2), color, thickness)
    return out_img


def export_to_json(detections: list[Detection], output_path: Path):
    """Exports detections to a JSON file."""
    data = []
    for d in detections:
        data.append(
            {
                "class_id": d.class_id,
                "class_name": d.class_name,
                "confidence": float(d.confidence),
                "bbox": [d.box.xmin, d.box.ymin, d.box.xmax, d.box.ymax],
            }
        )
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)


def export_to_csv(detections: list[Detection], output_path: Path):
    """Exports detections to a CSV file."""
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["class_id", "class_name", "confidence", "xmin", "ymin", "xmax", "ymax"]
        )
        for d in detections:
            writer.writerow(
                [
                    d.class_id,
                    d.class_name,
                    f"{d.confidence:.4f}",
                    d.box.xmin,
                    d.box.ymin,
                    d.box.xmax,
                    d.box.ymax,
                ]
            )


def draw_count_summary(image: np.ndarray, summary: CountSummary) -> np.ndarray:
    """Draws counting summary on the image."""
    out_img = image.copy()

    text_lines = [f"Total Vehicles: {summary.total_vehicles}"]
    for cls_name, count in summary.class_counts.items():
        text_lines.append(f"{cls_name}: {count}")

    y_offset = 30
    for line in text_lines:
        cv2.putText(
            out_img,
            line,
            (20, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2,
        )
        y_offset += 30

    return out_img
