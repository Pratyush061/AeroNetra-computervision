"""Unit tests for ground-truth loaders."""

from pathlib import Path

from aeronetra.evaluation.groundtruth import (
    image_sizes_from_dir,
    load_visdrone_ground_truth,
    load_yolo_ground_truth,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_load_yolo_ground_truth(tmp_path):
    labels_dir = tmp_path / "labels"
    labels_dir.mkdir()
    (labels_dir / "img1.txt").write_text(
        "# comment\n0 0.5 0.5 0.2 0.2\n1 0.1 0.1 0.05 0.05\nmalformed\n",
        encoding="utf-8",
    )

    ground_truth = load_yolo_ground_truth(labels_dir, {"img1": (1000, 1000)})
    objects = ground_truth.images["img1"].objects

    assert len(objects) == 2
    assert objects[0].class_id == 0
    assert objects[0].box.xyxy == (400.0, 400.0, 600.0, 600.0)


def test_load_yolo_ground_truth_skips_unknown_images(tmp_path):
    labels_dir = tmp_path / "labels"
    labels_dir.mkdir()
    (labels_dir / "img1.txt").write_text("0 0.5 0.5 0.2 0.2\n", encoding="utf-8")

    ground_truth = load_yolo_ground_truth(labels_dir, {})

    assert ground_truth.images == {}


def test_load_visdrone_ground_truth_keeps_only_valid_vehicles(tmp_path):
    labels_dir = tmp_path / "labels"
    labels_dir.mkdir()
    # car (4) valid, pedestrian (1) dropped, zero-area van (5) dropped
    (labels_dir / "img1.txt").write_text(
        "10,10,20,20,1,4,0,0\n100,100,20,40,1,1,0,0\n200,200,0,0,1,5,0,0\n",
        encoding="utf-8",
    )

    ground_truth = load_visdrone_ground_truth(
        labels_dir, {"img1": (1000, 1000)}, mode="merged"
    )
    objects = ground_truth.images["img1"].objects

    assert len(objects) == 1
    assert objects[0].class_id == 0
    assert objects[0].box.xyxy == (10.0, 10.0, 30.0, 30.0)


def test_load_visdrone_ground_truth_separates_ignored_regions(tmp_path):
    labels_dir = tmp_path / "labels"
    labels_dir.mkdir()
    # a real car (category 4, score 1), an ignored region (category 0), and a
    # score-0 car row that the protocol excludes from evaluation.
    (labels_dir / "img1.txt").write_text(
        "10,10,20,20,1,4,0,0\n"
        "0,0,50,50,0,0,0,0\n"
        "300,300,20,20,0,4,0,0\n",
        encoding="utf-8",
    )

    ground_truth = load_visdrone_ground_truth(
        labels_dir, {"img1": (1000, 1000)}, mode="merged"
    )
    image = ground_truth.images["img1"]

    assert len(image.objects) == 1
    assert image.objects[0].box.xyxy == (10.0, 10.0, 30.0, 30.0)
    assert len(image.ignored) == 2
    assert ground_truth.total_objects() == 1
    assert len(image.ignore_boxes()) == 2


def test_image_sizes_from_dir():
    sizes = image_sizes_from_dir(FIXTURES / "images")

    assert sizes["0000001"] == (1000, 1000)
