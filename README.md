# AeroNetra

AeroNetra is a serious computer-vision research project dedicated to UAV and drone-based surveillance.
The repository is structured to support rigorous research and reproducible experiments.

## Current Milestone
**Detect and accurately count vehicles in aerial or drone images using object-detection models, bounding-box processing, and OpenCV.**

## Repository Structure
The project follows a standard data science/research structure:
- `configs/`: Configuration files for models and datasets
- `data/`: Dataset storage (excluded from git)
- `docs/`: Additional documentation and guides
- `notebooks/`: Jupyter notebooks for experiments and exploration
- `src/aeronetra/`: Reusable Python modules for core logic
- `tests/`: Unit and integration tests
- `scripts/`: Utility scripts
- `outputs/`: Generated artifacts (models, metrics, predictions)

## Setup
1. Create a virtual environment using Python 3.11.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   pip install -e .
   ```

## Usage
### Jupyter Notebooks
Launch Jupyter to access the environment check and experiment notebooks:
```bash
jupyter notebook
```
Follow the progression described in the notebooks (00 through 08).

### Running Tests
To run tests and linting:
```bash
ruff check .
pytest
```

## Datasets
Raw datasets should be placed in `data/raw/` or configured via the `DATASET_DIR` environment variable. Do not commit dataset files to version control.

## Excluded Files
Large files, datasets, trained weights, credentials, and generated images are intentionally excluded from version control to maintain a clean and lightweight repository.

## Planned Progression
1. **Phase 1:** Vehicle detection and image counting
2. **Phase 2:** Fine-tuning on aerial datasets
3. **Phase 3:** Video tracking and unique vehicle counting
4. **Phase 4:** Geospatial and traffic analytics
5. **Phase 5:** Edge deployment or integration with simulated UAV systems
