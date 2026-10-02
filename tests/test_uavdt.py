"""Unit tests for the UAVDT parser and converter.

The rows used here are synthetic and follow the documented UAVDT DET format;
they are not drawn from a real UAVDT download.
"""

from pathlib import Path

import pytest
from PIL import Image

from aeronetra.datasets.uavdt import (
    UAVDT_VEHICLE_CLASSES,
    convert_to_yolo_format,
    convert_uavdt_dataset,
    map_category,
    parse_uavdt_row,
)


def test_parse_uavdt_row_valid():
    parsed = parse_uavdt_row("1,7,100,200,50,60,0,1,1")

    assert parsed is not None
    assert parsed["frame_index"] == 1
    assert parsed["target_id"] == 7
    assert (parsed["left"], parsed["top"]) == (100, 200)
    assert (parsed["width"], parsed["height"]) == (50, 60)
    assert (parsed["out_of_view"], parsed["occlusion"]) == (0, 1)
    assert parsed["category"] == 1


def test_parse_uavdt_row_malformed():
    assert parse_uavdt_row("1,7,100") is None
    assert parse_uavdt_row("a,b,c,d,e,f,g,h,i") is None


def test_map_category():
    assert map_category(1, "merged") == 0
    assert map_category(3, "merged") == 0

    assert map_category(1, "separate") == 0
    assert map_category(2, "separate") == 1
    assert map_category(3, "separate") == 2

    # Category 0 and anything above the vehicle range are not vehicles.
    assert map_category(0, "separate") is None
    assert map_category(9, "separate") is None


def test_uavdt_vehicle_class_ids():
    assert UAVDT_VEHICLE_CLASSES == {1: "car", 2: "truck", 3: "bus"}


def test_convert_to_yolo_format():
    # 1080x540 frame; a 50x50 box at (100, 200).
    box = {"left": 100, "top": 200, "width": 50, "height": 50}
    yolo = convert_to_yolo_format(box, 1080, 540)

    assert yolo is not None
    assert yolo[0] == pytest.approx((100 + 25) / 1080)
    assert yolo[1] == pytest.approx((200 + 25) / 540)
    assert yolo[2] == pytest.approx(50 / 1080)
    assert yolo[3] == pytest.approx(50 / 540)


def test_convert_to_yolo_format_clips_and_rejects():
    # Partially outside the frame is clipped, not dropped.
    clipped = convert_to_yolo_format(
        {"left": -20, "top": 10, "width": 50, "height": 50}, 1080, 540
    )
    assert clipped is not None
    assert clipped[2] == pytest.approx(30 / 1080)

    # Zero-area and fully-outside boxes are rejected.
    assert convert_to_yolo_format(
        {"left": 10, "top": 10, "width": 0, "height": 50}, 1080, 540
    ) is None
    assert convert_to_yolo_format(
        {"left": -100, "top": 10, "width": 50, "height": 50}, 1080, 540
    ) is None


def _make_sequence(tmp_path: Path) -> tuple[Path, Path]:
    """Build a tiny synthetic UAVDT sequence layout and return (images, gt)."""
    images_root = tmp_path / "UAV-benchmark-M"
    gt_dir = tmp_path / "GT"
    sequence_dir = images_root / "M0101"
    sequence_dir.mkdir(parents=True)
    gt_dir.mkdir(parents=True)

    Image.new("RGB", (1080, 540)).save(sequence_dir / "img000001.jpg")
    Image.new("RGB", (1080, 540)).save(sequence_dir / "img000002.jpg")

    # Frame 1: a car and a bus. Frame 2: one truck, plus a non-vehicle row.
    gt_dir.joinpath("M0101_gt_whole.txt").write_text(
        "1,1,100,200,50,50,0,0,1\n"
        "1,2,300,100,40,40,0,0,3\n"
        "2,3,10,10,20,20,0,0,2\n"
        "2,4,5,5,10,10,0,0,9\n",
        encoding="utf-8",
    )
    return images_root, gt_dir


def test_convert_uavdt_dataset_end_to_end(tmp_path):
    images_root, gt_dir = _make_sequence(tmp_path)
    output_dir = tmp_path / "out"

    stats = convert_uavdt_dataset(
        images_root, gt_dir, output_dir, mode="separate", dry_run=False
    )

    assert stats["sequences"] == 1
    assert stats["total_images"] == 2
    assert stats["valid_annotations"] == 3
    assert stats["ignored_annotations"] == 1
    assert stats["missing_images"] == 0

    label_file = output_dir / "labels" / "M0101_000001.txt"
    assert label_file.exists()
    lines = label_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    # separate mode: car = 0, bus = 2
    assert lines[0].startswith("0 ")
    assert lines[1].startswith("2 ")
    assert (output_dir / "images" / "M0101_000001.jpg").exists()


def test_convert_uavdt_dataset_dry_run_writes_nothing(tmp_path):
    images_root, gt_dir = _make_sequence(tmp_path)
    output_dir = tmp_path / "out"

    stats = convert_uavdt_dataset(images_root, gt_dir, output_dir, dry_run=True)

    assert stats["valid_annotations"] == 3
    assert not output_dir.exists()


def test_convert_uavdt_dataset_reports_missing_images(tmp_path):
    images_root, gt_dir = _make_sequence(tmp_path)
    # Remove the frame-2 image so its annotations cannot be converted.
    (images_root / "M0101" / "img000002.jpg").unlink()

    stats = convert_uavdt_dataset(images_root, gt_dir, tmp_path / "out", dry_run=True)

    assert stats["missing_images"] == 1
    assert stats["total_images"] == 1
