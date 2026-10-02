"""UAVDT dataset parsing and conversion utilities.

UAVDT (UAV Detection and Tracking benchmark, Du et al., ECCV 2018) is a
sequence-based aerial vehicle benchmark. Unlike VisDrone, annotations live in
one ground-truth file per sequence rather than one label file per image.

.. warning::
   This adapter is implemented from the publicly documented UAVDT format — the
   DET ground-truth files (``*_gt_whole.txt``) and the ``UAV-benchmark-M``
   sequence layout — and has **not** been verified against a real UAVDT
   download. Treat the column mapping and class ids as provisional until they
   are checked against the actual dataset. The DET ``_gt_whole`` files are the
   intended source; the MOT (``*_gt.txt``) and ignore (``*_gt_ignore.txt``)
   files are deliberately not read here.

Documented DET row format (``<sequence>_gt_whole.txt``)::

    <frame_index>,<target_id>,<bbox_left>,<bbox_top>,<bbox_width>,<bbox_height>,
    <out_of_view>,<occlusion>,<object_category>

Vehicle categories are 1-based: 1 = car, 2 = truck, 3 = bus. Frames are stored
as ``<images_root>/<sequence>/img<frame_index:06d>.jpg``.
"""

import logging
import os
import shutil
from pathlib import Path

from PIL import Image

from aeronetra.counting.ops import clip_box
from aeronetra.detection.types import BoundingBox

logger = logging.getLogger(__name__)

# UAVDT DET categories are 1-based (the benchmark's `object_category` field).
UAVDT_VEHICLE_CLASSES = {
    1: "car",
    2: "truck",
    3: "bus",
}

# frame_index, target_id, bbox_left, bbox_top, bbox_width, bbox_height,
# out_of_view, occlusion, object_category
_UAVDT_FIELD_COUNT = 9
_GT_SUFFIX = "_gt_whole.txt"

_ROW_KEYS = (
    "frame_index",
    "target_id",
    "left",
    "top",
    "width",
    "height",
    "out_of_view",
    "occlusion",
    "category",
)

_SEPARATE_MAP = {1: 0, 2: 1, 3: 2}


def parse_uavdt_row(row_str: str) -> dict[str, int] | None:
    """Parse one row of a UAVDT DET ground-truth file.

    Args:
        row_str: A comma-separated annotation line.

    Returns:
        A dict keyed by :data:`_ROW_KEYS`, or ``None`` if the row is malformed.
    """
    parts = row_str.strip().split(",")
    if len(parts) < _UAVDT_FIELD_COUNT:
        return None
    try:
        values = [int(part) for part in parts[:_UAVDT_FIELD_COUNT]]
    except ValueError:
        return None
    return dict(zip(_ROW_KEYS, values))


def map_category(category: int, mode: str = "separate") -> int | None:
    """Map a UAVDT category id to a YOLO class id.

    Args:
        category: UAVDT category (1 = car, 2 = truck, 3 = bus).
        mode: ``"merged"`` maps every vehicle to class 0; ``"separate"`` maps to
            sequential ids (car = 0, truck = 1, bus = 2).

    Returns:
        The YOLO class id, or ``None`` if the category is not a vehicle.
    """
    if category not in UAVDT_VEHICLE_CLASSES:
        return None
    if mode == "merged":
        return 0
    if mode == "separate":
        return _SEPARATE_MAP[category]
    return None


def convert_to_yolo_format(
    box: dict[str, int], img_width: int, img_height: int
) -> tuple[float, float, float, float] | None:
    """Convert a UAVDT box to normalized YOLO ``(x_center, y_center, w, h)``.

    The box is clipped to the image boundary; a box with no area after clipping
    returns ``None``.
    """
    if box["width"] <= 0 or box["height"] <= 0:
        return None

    xmin, ymin = box["left"], box["top"]
    clipped = clip_box(
        BoundingBox(xmin, ymin, xmin + box["width"], ymin + box["height"]),
        img_width,
        img_height,
    )
    if clipped.width <= 0 or clipped.height <= 0:
        return None

    x_center = (clipped.xmin + clipped.width / 2) / img_width
    y_center = (clipped.ymin + clipped.height / 2) / img_height
    return (x_center, y_center, clipped.width / img_width, clipped.height / img_height)


def _image_size(path: Path) -> tuple[int, int] | None:
    """Return ``(width, height)`` from an image header, or ``None`` if unreadable."""
    try:
        with Image.open(path) as image:
            return image.size
    except OSError:
        return None


def convert_uavdt_dataset(
    images_root: Path,
    gt_dir: Path,
    output_dir: Path,
    mode: str = "separate",
    dry_run: bool = False,
) -> dict[str, int]:
    """Convert a UAVDT sequence split to YOLO format.

    Args:
        images_root: Directory holding one sub-directory per sequence, e.g.
            ``UAV-benchmark-M/M0101/img000001.jpg``.
        gt_dir: Directory holding the DET ground-truth files, e.g.
            ``UAV-benchmark-MOTD_v1.0/GT/M0101_gt_whole.txt``.
        output_dir: Destination for the YOLO ``images/`` and ``labels/`` trees.
        mode: ``"merged"`` or ``"separate"`` class mapping.
        dry_run: If True, compute statistics without writing files.

    Returns:
        Conversion statistics, including the number of sequences processed.
    """
    stats = {
        "sequences": 0,
        "total_images": 0,
        "valid_annotations": 0,
        "ignored_annotations": 0,
        "malformed_annotations": 0,
        "skipped_zero_area": 0,
        "missing_images": 0,
    }

    if not gt_dir.exists():
        return stats

    out_images_dir = output_dir / "images"
    out_labels_dir = output_dir / "labels"
    if not dry_run:
        # NOTE: once the utils package lands, this can use aeronetra.utils.paths.ensure_dir.
        out_images_dir.mkdir(parents=True, exist_ok=True)
        out_labels_dir.mkdir(parents=True, exist_ok=True)

    for gt_path in sorted(gt_dir.glob(f"*{_GT_SUFFIX}")):
        sequence = gt_path.name[: -len(_GT_SUFFIX)]
        stats["sequences"] += 1
        sequence_dir = images_root / sequence

        # One ground-truth file spans a whole sequence, so group rows by frame
        # to produce one label file per frame.
        frames: dict[int, list[dict[str, int]]] = {}
        for row in gt_path.read_text(encoding="utf-8").splitlines():
            parsed = parse_uavdt_row(row)
            if not parsed:
                stats["malformed_annotations"] += 1
                continue
            class_id = map_category(parsed["category"], mode)
            if class_id is None:
                stats["ignored_annotations"] += 1
                continue
            frames.setdefault(parsed["frame_index"], []).append(
                {**parsed, "class_id": class_id}
            )

        for frame_index, objects in sorted(frames.items()):
            image_path = sequence_dir / f"img{frame_index:06d}.jpg"
            size = _image_size(image_path) if image_path.exists() else None
            if size is None:
                stats["missing_images"] += 1
                continue
            img_width, img_height = size

            lines = []
            for obj in objects:
                yolo_box = convert_to_yolo_format(obj, img_width, img_height)
                if yolo_box is None:
                    stats["skipped_zero_area"] += 1
                    continue
                stats["valid_annotations"] += 1
                xc, yc, w, h = yolo_box
                lines.append(f"{obj['class_id']} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n")

            stats["total_images"] += 1
            if dry_run:
                continue

            # Frame filenames repeat across sequences, so namespace the outputs.
            stem = f"{sequence}_{frame_index:06d}"
            (out_labels_dir / f"{stem}.txt").write_text("".join(lines), encoding="utf-8")
            out_image_path = out_images_dir / f"{stem}.jpg"
            if not out_image_path.exists():
                try:
                    os.symlink(image_path.resolve(), out_image_path)
                except OSError:
                    shutil.copy2(image_path, out_image_path)

    return stats
