"""Logging configuration shared by scripts and notebooks."""

import logging

_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def configure_logging(level: int | str = logging.INFO) -> None:
    """Configure the root logger with a consistent format and level.

    Library modules already log via ``logging.getLogger(__name__)``; this gives
    callers (scripts, notebooks) one place to decide how much they see.

    Args:
        level: A ``logging`` level constant or its name (e.g. ``"DEBUG"``).

    Raises:
        ValueError: If a string level name is not recognised.
    """
    if isinstance(level, str):
        resolved = logging.getLevelName(level.upper())
        if not isinstance(resolved, int):
            raise ValueError(f"Unknown logging level: {level!r}")
        level = resolved

    logging.basicConfig(format=_LOG_FORMAT, level=level)
    logging.getLogger().setLevel(level)
