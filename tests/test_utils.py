"""Unit tests for the shared utilities package."""

import logging
import random
from pathlib import Path

import numpy as np
import pytest

from aeronetra.utils import configure_logging, ensure_dir, set_seed


def test_set_seed_reproduces_python_and_numpy_streams():
    set_seed(123)
    first = (random.random(), float(np.random.rand()))
    set_seed(123)
    second = (random.random(), float(np.random.rand()))

    assert first == second


def test_set_seed_folds_out_of_range_seeds():
    # NumPy's legacy seed only accepts [0, 2**32 - 1]; set_seed must not raise.
    set_seed(-1)
    set_seed(2**40)


def test_set_seed_works_without_torch():
    # torch is an optional backend; seeding must still succeed when it is absent.
    set_seed(0)
    set_seed(0, deterministic_cudnn=True)


def test_ensure_dir_creates_nested_path_and_is_idempotent(tmp_path):
    target = tmp_path / "a" / "b" / "c"

    assert ensure_dir(target) == target
    assert target.is_dir()
    assert ensure_dir(target) == target


def test_ensure_dir_accepts_a_string(tmp_path):
    target = str(tmp_path / "x" / "y")

    result = ensure_dir(target)

    assert isinstance(result, Path)
    assert Path(target).is_dir()


def test_configure_logging_accepts_name_and_sets_level():
    configure_logging("WARNING")

    assert logging.getLogger().level == logging.WARNING


def test_configure_logging_rejects_unknown_level():
    with pytest.raises(ValueError, match="Unknown logging level"):
        configure_logging("NOT_A_LEVEL")
