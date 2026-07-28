#!/usr/bin/env python3
"""
Dataset Validation CLI.
Validates YOLO format dataset for errors.
"""
import argparse
import json
from pathlib import Path
import cv2

def validate_dataset(dataset_name: str, images_dir: Path, labels_dir: Path):
    report = {
        "dataset": dataset_name,
        "total_images": 0,
        "missing_pairs": 0,
        "unreadable_images": 0,
        "malformed_labels": 0,
        "zero_area_boxes": 0,
        "out_of_bounds_boxes": 0,
        "invalid_class_ids": 0,
        "duplicate_rows": 0,
        "suspiciously_tiny_boxes": 0,
        "extreme_aspect_ratios": 0,
        "class_counts": {}
    }

    if not images_dir.exists():
        print(f"Error: Images directory not found: {images_dir}")
        return
    if not labels_dir.exists():
        print(f"Error: Labels directory not found: {labels_dir}")
        return

    for img_path in images_dir.glob("*.jpg"):
        report["total_images"] += 1
        label_path = labels_dir / f"{img_path.stem}.txt"

        if not label_path.exists():
            report["missing_pairs"] += 1
            continue

        img = cv2.imread(str(img_path))
        if img is None:
            report["unreadable_images"] += 1
            continue

        img_h, img_w = img.shape[:2]
        seen_rows = set()

        try:
            with open(label_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    if line in seen_rows:
                        report["duplicate_rows"] += 1
                        continue
                    seen_rows.add(line)

                    parts = line.split()
                    if len(parts) != 5:
                        report["malformed_labels"] += 1
                        continue

                    try:
                        c, x, y, w, h = map(float, parts)
                        c = int(c)
                    except ValueError:
                        report["malformed_labels"] += 1
                        continue

                    if c < 0:
                        report["invalid_class_ids"] += 1

                    report["class_counts"][c] = report["class_counts"].get(c, 0) + 1

                    if w <= 0 or h <= 0:
                        report["zero_area_boxes"] += 1
                        continue

                    # Normalized bounds check
                    if x - w/2 < 0 or y - h/2 < 0 or x + w/2 > 1 or y + h/2 > 1:
                        report["out_of_bounds_boxes"] += 1

                    if w * img_w < 5 or h * img_h < 5:
                        report["suspiciously_tiny_boxes"] += 1

                    aspect_ratio = (w * img_w) / (h * img_h)
                    if aspect_ratio > 10 or aspect_ratio < 0.1:
                        report["extreme_aspect_ratios"] += 1

        except (ValueError, IndexError, OSError):
            report["malformed_labels"] += 1

    print("=== Validation Report ===")
    for k, v in report.items():
        if k != "class_counts":
            print(f"{k.replace('_', ' ').capitalize()}: {v}")

    print("\nClass Counts:")
    for c, count in sorted(report["class_counts"].items()):
        print(f"  Class {c}: {count}")

    print("\nJSON Output:")
    print(json.dumps(report, indent=2))

def main():
    parser = argparse.ArgumentParser(description="Validate YOLO format dataset.")
    parser.add_argument("--dataset", required=True, help="Name of the dataset")
    parser.add_argument("--images", required=True, help="Path to images directory")
    parser.add_argument("--labels", required=True, help="Path to labels directory")
    args = parser.parse_args()

    validate_dataset(args.dataset, Path(args.images), Path(args.labels))

if __name__ == "__main__":
    main()
