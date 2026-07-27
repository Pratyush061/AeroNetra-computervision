# Datasets Guide

This document outlines the usage and structure for datasets within the AeroNetra project.

## Directory Structure
- `data/raw/`: Original, unmodified datasets.
- `data/interim/`: Intermediate data that has been transformed.
- `data/processed/`: Final, processed data ready for modeling.
- `data/samples/`: Small sample subsets for quick testing and debugging.

## Handling Rules
- Do not commit datasets to version control.
- Ensure datasets are handled properly and configured via environment variables (e.g., `DATASET_DIR`).
- Never automatically download large datasets in scripts or notebooks.
