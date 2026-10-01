from pathlib import Path

import cv2
import numpy as np

from scripts.validate_dataset import validate_dataset


def test_validate_dataset_basic(tmp_path: Path):
    images_dir = tmp_path / "images"
    labels_dir = tmp_path / "labels"
    images_dir.mkdir()
    labels_dir.mkdir()

    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.imwrite(str(images_dir / "001.jpg"), img)

    labels = [
        "0 0.5 0.5 0.2 0.2",
        "1 0.3 0.3 0.1 0.1",
    ]
    (labels_dir / "001.txt").write_text("\n".join(labels), encoding="utf-8")

    report = validate_dataset("visdrone_test", images_dir, labels_dir, num_classes=8)
    assert report["total_images"] == 1
    assert report["valid_labels"] == 2
    assert report["missing_labels"] == 0
    assert report["out_of_bounds_boxes"] == 0
    assert report["malformed_labels"] == 0
    assert report["class_counts"][0] == 1
    assert report["class_counts"][1] == 1


def test_validate_dataset_anomalies(tmp_path: Path):
    images_dir = tmp_path / "images"
    labels_dir = tmp_path / "labels"
    images_dir.mkdir()
    labels_dir.mkdir()

    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.imwrite(str(images_dir / "sample.jpg"), img)

    labels = [
        "0 0.5 0.5 0.2 0.2",
        "0 0.5 0.5 0.2 0.2",
        "1 0.01 0.5 0.2 0.2",
        "2 0.5 0.5 0.001 0.001",
        "3 0.5 0.5 0.9 0.01",
        "9 0.5 0.5 0.1 0.1",
        "malformed line",
    ]
    (labels_dir / "sample.txt").write_text("\n".join(labels), encoding="utf-8")

    report = validate_dataset("anomaly_test", images_dir, labels_dir, num_classes=8)
    assert report["total_images"] == 1
    assert report["duplicate_rows"] == 1
    assert report["out_of_bounds_boxes"] == 1
    assert report["suspiciously_tiny_boxes"] == 1
    assert report["extreme_aspect_ratios"] == 1
    assert report["invalid_class_ids"] == 1
    assert report["malformed_labels"] == 1


def test_validate_dataset_missing_dirs(tmp_path: Path):
    report = validate_dataset(
        "missing_test",
        tmp_path / "nonexistent_img",
        tmp_path / "nonexistent_lbl",
    )
    assert report["total_images"] == 0
