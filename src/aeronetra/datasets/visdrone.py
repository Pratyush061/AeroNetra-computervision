"""
VisDrone dataset parsing and conversion utilities.
Converts standard VisDrone annotations to YOLO format.
"""
from pathlib import Path
from typing import Dict, Tuple, Optional
import cv2
import os

# Original VisDrone Classes:
# 0: ignored regions, 1: pedestrian, 2: people, 3: bicycle, 4: car, 5: van
# 6: truck, 7: tricycle, 8: awning-tricycle, 9: bus, 10: motor, 11: others
VISDRONE_VEHICLE_CLASSES = {
    3: "bicycle",
    4: "car",
    5: "van",
    6: "truck",
    7: "tricycle",
    8: "awning-tricycle",
    9: "bus",
    10: "motor"
}

def parse_visdrone_row(row_str: str) -> Optional[Dict[str, int]]:
    """
    Parses a single row from a VisDrone annotation file.
    Format: <bbox_left>,<bbox_top>,<bbox_width>,<bbox_height>,<score>,<object_category>,<truncation>,<occlusion>
    """
    parts = row_str.strip().split(',')
    if len(parts) < 8:
        return None
    try:
        return {
            'left': int(parts[0]),
            'top': int(parts[1]),
            'width': int(parts[2]),
            'height': int(parts[3]),
            'score': int(parts[4]),
            'category': int(parts[5]),
            'truncation': int(parts[6]),
            'occlusion': int(parts[7])
        }
    except ValueError:
        return None

def map_category(category: int, mode: str = "separate") -> Optional[int]:
    """
    Maps VisDrone category to project class ID.
    Returns None if category is ignored.
    """
    # Exclude non-vehicles (0=ignored, 1=pedestrian, 2=people, 11=others)
    if category not in VISDRONE_VEHICLE_CLASSES and category != 4: # keep 4 for car just in case
        pass

    # Check explicitly
    if category in [0, 1, 2, 11]:
        return None

    if mode == "merged":
        return 0 # All vehicles are class 0
    elif mode == "separate":
        # Map [3, 4, 5, 6, 7, 8, 9, 10] -> [0, 1, 2, 3, 4, 5, 6, 7]
        # Just use order for separation. We will assume 0=car, 1=van etc for YOLO
        # The exact mapping depends on YAML, but for code we can map to 0..N
        mapping = {4: 0, 5: 1, 6: 2, 7: 3, 8: 4, 9: 5, 10: 6, 3: 7} # Assuming bicycle=7
        return mapping.get(category)
    return None

def convert_to_yolo_format(box: Dict[str, int], img_width: int, img_height: int) -> Optional[Tuple[float, float, float, float]]:
    """
    Converts VisDrone box to normalized YOLO format (x_center, y_center, width, height).
    Clips to image boundaries and rejects invalid boxes.
    """
    left = max(0, box['left'])
    top = max(0, box['top'])
    right = min(img_width, box['left'] + box['width'])
    bottom = min(img_height, box['top'] + box['height'])

    w = right - left
    h = bottom - top

    if w <= 0 or h <= 0:
        return None

    x_center = (left + w / 2) / img_width
    y_center = (top + h / 2) / img_height
    norm_w = w / img_width
    norm_h = h / img_height

    # Final safety check
    x_center = min(max(x_center, 0.0), 1.0)
    y_center = min(max(y_center, 0.0), 1.0)
    norm_w = min(max(norm_w, 0.0), 1.0)
    norm_h = min(max(norm_h, 0.0), 1.0)

    return (x_center, y_center, norm_w, norm_h)


def convert_dataset(images_dir: Path, labels_dir: Path, output_dir: Path, mode: str = "separate", dry_run: bool = False) -> Dict[str, int]:
    """
    Converts a directory of VisDrone images and labels to YOLO format.
    Saves in output_dir/images and output_dir/labels.
    Returns conversion summary statistics.
    """
    stats = {
        'total_images': 0,
        'missing_labels': 0,
        'valid_annotations': 0,
        'ignored_annotations': 0,
        'malformed_annotations': 0,
        'skipped_zero_area': 0
    }

    if not images_dir.exists():
        return stats

    out_images_dir = output_dir / "images"
    out_labels_dir = output_dir / "labels"

    if not dry_run:
        out_images_dir.mkdir(parents=True, exist_ok=True)
        out_labels_dir.mkdir(parents=True, exist_ok=True)

    # Deterministic sorting
    image_paths = sorted(images_dir.glob("*.jpg"))
    stats['total_images'] = len(image_paths)

    for img_path in image_paths:
        label_path = labels_dir / f"{img_path.stem}.txt"
        out_label_path = out_labels_dir / f"{img_path.stem}.txt"
        out_img_path = out_images_dir / img_path.name

        if not label_path.exists():
            stats['missing_labels'] += 1
            continue

        try:
            # We must read the image to get dimensions for normalization
            # In a dry_run, we still read it to calculate stats properly.
            img = cv2.imread(str(img_path))
            if img is None:
                stats['malformed_annotations'] += 1
                continue
            img_h, img_w = img.shape[:2]
        except (ValueError, IndexError, OSError, cv2.error):
            stats['malformed_annotations'] += 1
            continue

        yolo_lines = []
        with open(label_path, 'r', encoding='utf-8') as f:
            for line in f:
                parsed = parse_visdrone_row(line)
                if not parsed:
                    stats['malformed_annotations'] += 1
                    continue

                cat_id = map_category(parsed['category'], mode)
                if cat_id is None:
                    stats['ignored_annotations'] += 1
                    continue

                yolo_box = convert_to_yolo_format(parsed, img_w, img_h)
                if not yolo_box:
                    stats['skipped_zero_area'] += 1
                    continue

                stats['valid_annotations'] += 1
                xc, yc, w, h = yolo_box
                yolo_lines.append(f"{cat_id} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n")

        if not dry_run:
            with open(out_label_path, 'w', encoding='utf-8') as f:
                f.writelines(yolo_lines)

            # Symlink or copy image. Symlink is faster and saves space, but copying is safer.
            # Let's symlink if possible, else copy.
            if not out_img_path.exists():
                try:
                    os.symlink(img_path.resolve(), out_img_path)
                except OSError:
                    import shutil
                    shutil.copy2(img_path, out_img_path)

    return stats
