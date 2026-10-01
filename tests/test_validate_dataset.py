"""Unit tests for the dataset validation CLI (scripts/validate_dataset.py)."""

import cv2
import numpy as np
import pytest

from scripts.validate_dataset import validate_dataset


def _write_image(path, size=(100, 100)):
    cv2.imwrite(str(path), np.zeros((size[1], size[0], 3), dtype=np.uint8))


@pytest.fixture
def dataset(tmp_path):
    """Returns an (images_dir, labels_dir) pair inside a temp directory."""
    images, labels = tmp_path / "images", tmp_path / "labels"
    images.mkdir()
    labels.mkdir()
    return images, labels


def test_valid_labels_are_counted(dataset):
    images, labels = dataset
    _write_image(images / "a.jpg")
    (labels / "a.txt").write_text("0 0.5 0.5 0.2 0.2\n")

    report = validate_dataset("ds", images, labels, num_classes=8)

    assert report["total_images"] == 1
    assert report["malformed_labels"] == 0
    assert report["class_counts"] == {0: 1}


def test_missing_label_pair(dataset):
    images, labels = dataset
    _write_image(images / "a.jpg")

    assert validate_dataset("ds", images, labels)["missing_pairs"] == 1


def test_malformed_and_duplicate_rows(dataset):
    images, labels = dataset
    _write_image(images / "a.jpg")
    (labels / "a.txt").write_text(
        "0 0.5 0.5 0.2 0.2\n"  # valid
        "0 0.5 0.5 0.2 0.2\n"  # duplicate of the previous row
        "0 0.5 0.5\n"  # too few fields
    )

    report = validate_dataset("ds", images, labels)

    assert report["duplicate_rows"] == 1
    assert report["malformed_labels"] == 1


def test_out_of_bounds_and_tiny_boxes(dataset):
    images, labels = dataset
    _write_image(images / "a.jpg")
    (labels / "a.txt").write_text(
        "0 0.98 0.5 0.2 0.2\n"  # crosses the right edge
        "0 0.5 0.5 0.02 0.02\n"  # <5 px wide on a 100 px image
    )

    report = validate_dataset("ds", images, labels)

    assert report["out_of_bounds_boxes"] == 1
    assert report["suspiciously_tiny_boxes"] == 1


def test_invalid_class_id_flagged(dataset):
    images, labels = dataset
    _write_image(images / "a.jpg")
    (labels / "a.txt").write_text("9 0.5 0.5 0.2 0.2\n")

    assert validate_dataset("ds", images, labels, num_classes=8)["invalid_class_ids"] == 1


def test_missing_directories_returns_empty_report(tmp_path):
    report = validate_dataset("ds", tmp_path / "no_images", tmp_path / "no_labels")

    assert report["total_images"] == 0
    assert report["missing_pairs"] == 0
