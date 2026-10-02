"""Deterministic seeding for reproducible runs.

Randomness reaches an experiment from Python's ``random``, NumPy, and — when the
optional torch backend is installed — torch. Seeding all of them from one place
is what makes a run reproducible, which the Experiment Guide requires.
"""

import random

import numpy as np


def set_seed(seed: int) -> None:
    """Seed Python, NumPy and (when installed) torch.

    Args:
        seed: The integer seed to apply. Record it in ``InferenceMetadata`` so
            the run can be reproduced.
    """
    random.seed(seed)
    np.random.seed(seed)

    # torch is an optional backend (see pyproject.toml), so it is imported here
    # rather than at module load.
    try:
        import torch
    except ImportError:
        return

    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
