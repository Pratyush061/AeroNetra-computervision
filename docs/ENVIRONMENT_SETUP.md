# Environment Setup

To ensure reproducible research, use a consistent environment.

## Requirements
- Python >= 3.11
- Virtual environment (venv, conda)

## Setup Steps
1. Create and activate a Python 3.11 environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   pip install -e .
   ```
3. Copy `.env.example` to `.env` and fill in necessary configurations.
