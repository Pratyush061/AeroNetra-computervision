"""Reusable plotting utilities for dataset exploration and validation."""

from pathlib import Path

import matplotlib.pyplot as plt


def plot_class_distribution(
    class_counts: dict[int, int],
    class_names: dict[int, str],
    output_path: Path,
) -> None:
    """Plots a bar chart of class distributions."""
    classes = sorted(class_counts.keys())
    counts = [class_counts[c] for c in classes]
    names = [class_names.get(c, str(c)) for c in classes]

    plt.figure(figsize=(10, 6))
    bars = plt.bar(names, counts, color="skyblue")
    plt.title("Class Distribution")
    plt.xlabel("Class")
    plt.ylabel("Count")
    plt.xticks(rotation=45, ha="right")

    # Add values on top of bars
    for bar in bars:
        yval = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2, yval, int(yval), ha="center", va="bottom"
        )

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_size_distribution(
    sizes: list[int],
    title: str,
    xlabel: str,
    output_path: Path,
    bins: int = 50,
) -> None:
    """Plots a histogram of object sizes (width, height, area)."""
    plt.figure(figsize=(10, 6))
    plt.hist(sizes, bins=bins, color="coral", edgecolor="black")
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("Frequency")
    plt.grid(axis="y", alpha=0.75)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_objects_per_image(counts_per_image: list[int], output_path: Path) -> None:
    """Plots histogram of number of objects per image."""
    plt.figure(figsize=(10, 6))
    plt.hist(
        counts_per_image,
        bins=range(min(counts_per_image or [0]), max(counts_per_image or [1]) + 2, 1),
        color="lightgreen",
        edgecolor="black",
        align="left",
    )
    plt.title("Objects per Image Distribution")
    plt.xlabel("Number of Objects")
    plt.ylabel("Frequency")
    plt.grid(axis="y", alpha=0.75)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
