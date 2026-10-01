"""Unit tests for the plotting utilities (headless rendering)."""

from pathlib import Path

import matplotlib
import pytest

from aeronetra.visualization.plots import (
    plot_class_distribution,
    plot_objects_per_image,
    plot_size_distribution,
)


@pytest.fixture(autouse=True)
def _headless_matplotlib():
    matplotlib.use("Agg")


def _assert_png_written(path: Path) -> None:
    assert path.exists()
    assert path.stat().st_size > 0


def test_plot_class_distribution(tmp_path: Path):
    out = tmp_path / "class_dist.png"
    plot_class_distribution({0: 10, 1: 5, 2: 3}, {0: "car", 1: "van", 2: "truck"}, out)
    _assert_png_written(out)


def test_plot_size_distribution(tmp_path: Path):
    out = tmp_path / "size_dist.png"
    plot_size_distribution(
        [100, 200, 350, 400, 500], "Size Distribution", "Area (px^2)", out
    )
    _assert_png_written(out)


def test_plot_objects_per_image(tmp_path: Path):
    out = tmp_path / "objects_per_image.png"
    plot_objects_per_image([2, 5, 1, 0, 12, 3], out)
    _assert_png_written(out)
