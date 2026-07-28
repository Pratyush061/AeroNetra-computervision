import pytest
from pathlib import Path
from src.aeronetra.datasets.visdrone import parse_visdrone_row, map_category, convert_to_yolo_format, convert_dataset

def test_parse_visdrone_row():
    # Valid row
    row = "684,8,273,116,1,4,0,0"
    parsed = parse_visdrone_row(row)
    assert parsed is not None
    assert parsed['left'] == 684
    assert parsed['width'] == 273
    assert parsed['category'] == 4

    # Malformed row
    assert parse_visdrone_row("684,8,273") is None
    assert parse_visdrone_row("a,b,c,d,e,f,g,h") is None

def test_map_category():
    # Merged mode
    assert map_category(4, "merged") == 0 # car -> vehicle
    assert map_category(5, "merged") == 0 # van -> vehicle

    # Separate mode (using internal mapping 4->0, 5->1 etc.)
    assert map_category(4, "separate") == 0
    assert map_category(5, "separate") == 1

    # Ignored categories
    assert map_category(0, "separate") is None # ignored region
    assert map_category(1, "separate") is None # pedestrian
    assert map_category(11, "separate") is None # others

def test_convert_to_yolo_format():
    img_w, img_h = 1000, 1000

    # Normal box
    box = {'left': 100, 'top': 100, 'width': 200, 'height': 200}
    # center = (200, 200), w=200, h=200 -> norm_center=(0.2, 0.2), norm_wh=(0.2, 0.2)
    yolo = convert_to_yolo_format(box, img_w, img_h)
    assert yolo == (0.2, 0.2, 0.2, 0.2)

    # Box outside boundaries (negative left)
    box_out = {'left': -50, 'top': 100, 'width': 200, 'height': 200}
    # Clipped: left=0, top=100, width=150 (since right was -50+200=150)
    # center = (75, 200), w=150, h=200 -> norm = 0.075, 0.2, 0.15, 0.2
    yolo_out = convert_to_yolo_format(box_out, img_w, img_h)
    assert yolo_out is not None
    assert pytest.approx(yolo_out[0]) == 0.075
    assert pytest.approx(yolo_out[2]) == 0.15

    # Zero area after clipping
    box_zero = {'left': -200, 'top': 100, 'width': 100, 'height': 200}
    # right = -100. Clipped right = min(1000, -100) -> wait, right is min(1000, -100) which is -100.
    # But in logic right = min(img_width, left + width). -200+100=-100.
    # w = -100 - 0 = -100 <= 0 -> returns None
    assert convert_to_yolo_format(box_zero, img_w, img_h) is None

def test_convert_dataset(tmp_path):
    images_dir = Path("tests/fixtures/images")
    labels_dir = Path("tests/fixtures/labels")

    # Test Dry Run
    stats = convert_dataset(images_dir, labels_dir, tmp_path, mode="merged", dry_run=True)
    assert stats['total_images'] == 1
    # 0000001.txt has 6 rows:
    # 1 valid car, 1 ignored region, 1 pedestrian (ignored), 1 malformed, 1 zero area, 1 clipped out of bounds (which is valid after clipping)
    assert stats['valid_annotations'] == 2 # The car and the clipped box (if mapped correctly)
    assert stats['ignored_annotations'] >= 1
    assert stats['malformed_annotations'] >= 1
    assert stats['skipped_zero_area'] == 1

    # Test actual run
    stats = convert_dataset(images_dir, labels_dir, tmp_path, mode="merged", dry_run=False)
    assert (tmp_path / "images" / "0000001.jpg").exists()
    out_lbl = tmp_path / "labels" / "0000001.txt"
    assert out_lbl.exists()

    with open(out_lbl, 'r') as f:
        lines = f.readlines()
        assert len(lines) == 2 # Two valid annotations
        # Merged mode means class ID should be 0
        assert lines[0].startswith("0 ")
