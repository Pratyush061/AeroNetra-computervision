"""Loaders that turn on-disk annotations into a :class:`GroundTruth`."""

from collections.abc import Mapping
from pathlib import Path

from PIL import Image

from aeronetra.counting.ops import clip_box, convert_yolo_to_xyxy
from aeronetra.datasets.visdrone import map_category, parse_visdrone_row
from aeronetra.detection.types import BoundingBox
from aeronetra.evaluation.types import GroundTruth, GroundTruthObject

_IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png")


def image_sizes_from_dir(images_dir: Path) -> dict[str, tuple[int, int]]:
    """Return ``{image_id: (width, height)}`` for the images in a directory.

    Only image headers are read (via Pillow), so large evaluation sets do not
    pay to decode full pixel data.
    """
    sizes: dict[str, tuple[int, int]] = {}
    for path in sorted(images_dir.iterdir()):
        if path.suffix.lower() not in _IMAGE_SUFFIXES:
            continue
        try:
            with Image.open(path) as image:
                width, height = image.size
        except OSError:
            continue
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
    Ignored regions (category ``0``) and rows with score ``0`` are collected
    separately so the evaluator can exclude detections that fall inside them,
    matching the VisDrone protocol for those two cases.

    Args:
        labels_dir: Directory of VisDrone ``<image_id>.txt`` annotation files.
        image_sizes: ``{image_id: (width, height)}`` used to clip boxes.
        mode: ``"merged"`` (all vehicles → class 0) or ``"separate"``.

    Returns:
        A :class:`GroundTruth` whose ``objects`` are valid, non-empty vehicle
        boxes and whose ``ignored`` are the regions excluded from evaluation.
    """
    ground_truth = GroundTruth()
    for label_path in sorted(labels_dir.glob("*.txt")):
        size = image_sizes.get(label_path.stem)
        if size is None:
            continue
        width, height = size
        objects: list[GroundTruthObject] = []
        ignored: list[GroundTruthObject] = []
        for row in label_path.read_text(encoding="utf-8").splitlines():
            parsed = parse_visdrone_row(row)
            if not parsed:
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
            if box.area <= 0:
                continue
            class_id = map_category(parsed["category"], mode)
            # Ignored regions (category 0) and score-0 rows are excluded from
            # evaluation rather than dropped, so detections inside them are not
            # counted as false positives. Non-vehicle categories are dropped.
            if parsed["category"] == 0 or parsed["score"] == 0:
                ignored.append(
                    GroundTruthObject(class_id if class_id is not None else 0, box)
                )
                continue
            if class_id is None:
                continue
            objects.append(GroundTruthObject(class_id, box))
        ground_truth.add_image(label_path.stem, objects, ignored)
    return ground_truth
