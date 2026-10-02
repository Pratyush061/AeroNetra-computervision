"""Filesystem helpers shared across the pipeline."""

from pathlib import Path


def ensure_dir(path: Path | str) -> Path:
    """Create ``path`` and any missing parents, then return it as a ``Path``.

    Centralises the ``mkdir(parents=True, exist_ok=True)`` idiom used by the
    dataset converters and the report/export writers, so directory creation
    stays consistent and idempotent. Accepts a ``str`` or a ``Path``.
    """
    resolved = Path(path)
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved
