# Developer Guide for AeroNetra

Welcome to AeroNetra, a research project dedicated to UAV and drone-based surveillance. This guide will walk you through setting up your development environment, installing necessary dependencies, and understanding how to use the repository.

## 1. Prerequisites
- **Python 3.11** (strictly required, as the development environment targets this version).
- A virtual environment tool (like `venv` or `conda`).
- Git for cloning and version control.

## 2. Environment Setup

To ensure reproducible research, use a consistent environment.

### Step 2.1: Clone the Repository
```bash
git clone <repository_url>
cd <repository_directory>
```

### Step 2.2: Create a Virtual Environment
Create and activate a Python 3.11 virtual environment:

**Using venv:**
```bash
python3.11 -m venv venv
source venv/bin/activate  # On Linux/Mac
# venv\Scripts\activate   # On Windows
```

**Using conda:**
```bash
conda create -n aeronetra python=3.11
conda activate aeronetra
```

### Step 2.3: Install Dependencies
Install all required dependencies, development dependencies, and install the project in editable mode:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .
```

### Step 2.4: Environment Configuration
Copy the `.env.example` file to create your local `.env` configuration:
```bash
cp .env.example .env
```
Fill in any necessary configurations. Note: Raw datasets should be placed in `data/raw/` or configured via the `DATASET_DIR` environment variable. Never place Kaggle API keys or other secrets directly in the source code; use the `.env` file instead.

## 3. How to Use the Repository

The project follows a standard data science/research structure.

### Jupyter Notebooks
Experiments and explorations are conducted in Jupyter notebooks located in the `notebooks/` directory.
To launch Jupyter:
```bash
jupyter notebook
```
Follow the progression described in the notebooks (e.g., 00 through 08).

**Important Notebook Guidelines:**
- Notebooks should call library functions from `src/aeronetra/` instead of duplicating major logic.
- Keep notebook cells short and ordered.
- Model Inference Notebooks should be independent for each model architecture. Checkpoints must be loaded explicitly without training. Missing model APIs should fail clearly rather than silently substituting models.
- **Always clear notebook outputs** before committing to version control.

### Writing Code
- **Reusable Logic**: Any reusable Python modules (like core logic, bounding-box processing, dataset loaders) should be kept in `src/aeronetra/`.
- **Code Standards**: Python code must include docstrings, type hints, validation, and useful error messages.
- **OpenCV**: Use OpenCV for image loading, bounding-box drawing, geometric filtering, region-of-interest logic, and counting utilities.
- **No Frontend**: Never add frontend frameworks or website code unless explicitly requested.

### Running Tests and Linting
To ensure code quality and prevent regressions, run the following commands before submitting changes:
```bash
# Run linter
ruff check .

# Run unit tests
pytest
```
Ensure that all reusable modules have accompanying unit tests in the `tests/` directory.

## 4. Working with Data and Experiments

- **Do Not Commit Large Files**: Large files, raw datasets, trained weights, credentials, notebook outputs, generated images, and large experiment artifacts are intentionally excluded from version control to maintain a lightweight repository.
- **No Auto-Downloads**: Avoid downloading large files (datasets, model weights) automatically. Require explicit configuration.
- **Data Handling**: Preserve raw datasets and write conversions/outputs into `processed` directories. Convert bounding boxes to normalized YOLO format. Prefer official sources and handle ignored regions explicitly.
- **Experiment Metadata**: When running experiments, always record metadata: model name, package version, weights, dataset version, image size, confidence threshold, IoU threshold, deterministic random seed, device, and timing.
- **No Fabrication**: Never fabricate benchmark results, completed training runs, model metrics, or dataset paths. Clearly distinguish between implemented, locally tested, statically validated, and unexecuted code.
- **Model Evaluation**: Do not claim a model is "best" without measured evidence from a shared validation split.
- **Counting Methodology**: Distinguish between image-level vehicle counting (detections, class count, total vehicle count) and unique vehicle count across video (which requires tracking). Never describe frame-by-frame detections as unique traffic counts.

By following these guidelines, you will help maintain a clean, lightweight, and rigorous research repository.
