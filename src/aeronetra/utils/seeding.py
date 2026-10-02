"""Deterministic seeding for reproducible runs.

Randomness reaches an experiment from Python's ``random``, NumPy, and — when the
optional torch backend is installed — torch. Seeding all of them from one place
is what makes a run reproducible, which the Experiment Guide requires.
"""

import random

import numpy as np

# NumPy's legacy seed only accepts [0, 2**32 - 1] while ``random`` and torch take
# the full integer range, so seeds are folded into that window to keep a single
# seed usable across every backend.
_NUMPY_SEED_MAX = 2**32


def set_seed(seed: int, deterministic_cudnn: bool = False) -> None:
    """Seed Python, NumPy and (when installed) torch.

    Args:
        seed: The integer seed to apply. Record it in ``InferenceMetadata`` so
            the run can be reproduced.
        deterministic_cudnn: When True and a CUDA device is present, also force
            deterministic cuDNN behaviour (disabling the benchmark autotuner).
            This trades throughput for reproducibility.
    """
    random.seed(seed)
    np.random.seed(seed % _NUMPY_SEED_MAX)

    # torch is an optional backend (see pyproject.toml), so it is imported here
    # rather than at module load.
    try:
        import torch
    except ImportError:
        return

    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        if deterministic_cudnn:
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
