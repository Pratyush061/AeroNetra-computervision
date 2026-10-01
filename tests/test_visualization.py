from pathlib import Path

import matplotlib
import pytest

from aeronetra.visualization.plots import (
    plot_class_distribution,
    plot_objects_per_image,
    plot_size_distribution,
)


@pytest.fixture(autouse=True)
def _setup_matplotlib_backend():
    matplotlib.use("Agg")


def test_plot_class_distribution(tmp_path: Path):
    output_file = tmp_path / "class_dist.png"
    class_counts = {0: 10, 1: 5, 2: 3}
    class_names = {0: "car", 1: "van", 2: "truck"}
    plot_class_distribution(class_counts, class_names, output_file)
    assert output_file.exists()
    assert output_file.stat().st_size > 0


def test_plot_size_distribution(tmp_path: Path):
    output_file = tmp_path / "size_dist.png"
    sizes = [100, 200, 350, 400, 500]
    plot_size_distribution(
        sizes, "Size Distribution", "Area (pixels^2)", output_file
    )
    assert output_file.exists()
    assert output_file.stat().st_size > 0


def test_plot_objects_per_image(tmp_path: Path):
    output_file = tmp_path / "objects_per_image.png"
    counts = [2, 5, 1, 0, 12, 3]
    plot_objects_per_image(counts, output_file)
    assert output_file.exists()
    assert output_file.stat().st_size > 0
