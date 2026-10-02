"""Filesystem helpers shared across the pipeline."""

from pathlib import Path


def ensure_dir(path: Path) -> Path:
    """Create ``path`` and any missing parents, then return it.

    Centralises the ``mkdir(parents=True, exist_ok=True)`` idiom used by the
    dataset converters and the report/export writers, so directory creation
    stays consistent and idempotent.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path
