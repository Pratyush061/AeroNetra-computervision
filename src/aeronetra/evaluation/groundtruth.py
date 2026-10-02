"""Loaders that turn on-disk annotations into a :class:`GroundTruth`."""

from collections.abc import Mapping
from pathlib import Path

import cv2

from aeronetra.counting.ops import clip_box, convert_yolo_to_xyxy
from aeronetra.datasets.visdrone import map_category, parse_visdrone_row
from aeronetra.detection.types import BoundingBox
from aeronetra.evaluation.types import GroundTruth, GroundTruthObject

_IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png")


def image_sizes_from_dir(images_dir: Path) -> dict[str, tuple[int, int]]:
    """Return ``{image_id: (width, height)}`` for the images in a directory."""
    sizes: dict[str, tuple[int, int]] = {}
    for path in sorted(images_dir.iterdir()):
        if path.suffix.lower() not in _IMAGE_SUFFIXES:
            continue
        image = cv2.imread(str(path))
        if image is None:
            continue
        height, width = image.shape[:2]
        sizes[path.stem] = (width, height)
    return sizes


def load_yolo_ground_truth(
    labels_dir: Path, image_sizes: Mapping[str, tuple[int, int]]
) -> GroundTruth:
    """Load YOLO-format labels (``class xc yc w h``, normalised) as ground truth.

    Args:
        labels_dir: Directory of ``<image_id>.txt`` label files.
        image_sizes: ``{image_id: (width, height)}`` used to denormalise boxes.

    Returns:
        A :class:`GroundTruth`. Label files without a matching image size are
        skipped, and malformed rows are ignored.
    """
    ground_truth = GroundTruth()
    for label_path in sorted(labels_dir.glob("*.txt")):
        size = image_sizes.get(label_path.stem)
        if size is None:
            continue
        width, height = size
        objects: list[GroundTruthObject] = []
        for row in label_path.read_text(encoding="utf-8").splitlines():
            row = row.strip()
            if not row or row.startswith("#"):
                continue
            parts = row.split()
            if len(parts) < 5:
                continue
            try:
                class_id = int(parts[0])
                xc, yc, nw, nh = (float(value) for value in parts[1:5])
                xmin, ymin, xmax, ymax = convert_yolo_to_xyxy(
                    xc, yc, nw, nh, width, height
                )
                box = clip_box(BoundingBox(xmin, ymin, xmax, ymax), width, height)
            except ValueError:
                continue
            if box.area > 0:
                objects.append(GroundTruthObject(class_id, box))
        ground_truth.add_image(label_path.stem, objects)
    return ground_truth


def load_visdrone_ground_truth(
    labels_dir: Path,
    image_sizes: Mapping[str, tuple[int, int]],
    mode: str = "separate",
) -> GroundTruth:
    """Load raw VisDrone annotations as ground truth.

    Only vehicle categories are kept; class ids follow the same mapping as the
    VisDrone converter (:func:`aeronetra.datasets.visdrone.map_category`).

    Args:
        labels_dir: Directory of VisDrone ``<image_id>.txt`` annotation files.
        image_sizes: ``{image_id: (width, height)}`` used to clip boxes.
        mode: ``"merged"`` (all vehicles → class 0) or ``"separate"``.

    Returns:
        A :class:`GroundTruth` containing only valid, non-empty vehicle boxes.
    """
    ground_truth = GroundTruth()
    for label_path in sorted(labels_dir.glob("*.txt")):
        size = image_sizes.get(label_path.stem)
        if size is None:
            continue
        width, height = size
        objects: list[GroundTruthObject] = []
        for row in label_path.read_text(encoding="utf-8").splitlines():
            parsed = parse_visdrone_row(row)
            if not parsed:
                continue
            class_id = map_category(parsed["category"], mode)
            if class_id is None:
                continue
            left, top = parsed["left"], parsed["top"]
            try:
                box = clip_box(
                    BoundingBox(left, top, left + parsed["width"], top + parsed["height"]),
                    width,
                    height,
                )
            except ValueError:
                continue
            if box.area > 0:
                objects.append(GroundTruthObject(class_id, box))
        ground_truth.add_image(label_path.stem, objects)
    return ground_truth
