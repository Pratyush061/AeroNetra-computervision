# Environment Setup

Detailed instructions for setting up the AeroNetra development environment.

---

## Requirements

- **Python 3.11** (strictly required)
- Virtual environment (`venv` or `conda`)
- Git
- (Optional) NVIDIA GPU with CUDA drivers for GPU-accelerated inference and training
- (Optional) Kaggle CLI for dataset downloads

---

## Step 1: Create and Activate a Virtual Environment

**Using venv (recommended):**
```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
```

**Using conda:**
```bash
conda create -n aeronetra python=3.11
conda activate aeronetra
```

---

## Step 2: Install Dependencies

```bash
pip install -r requirements.txt       # Runtime: torch, ultralytics, opencv-python, etc.
pip install -r requirements-dev.txt   # Development: pytest, ruff
pip install -e .                      # Install aeronetra as editable package
```

---

## Step 3: Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and configure the following:

| Variable | Required | Description |
|----------|----------|-------------|
| `DATASET_DIR` | Yes | Absolute path to your dataset root directory |
| `OUTPUT_DIR` | No | Custom output directory (defaults to `outputs/` in project root) |

If `DATASET_DIR` is not set, the code falls back to `data/raw/` in the project root.

> **Never** put secrets (API keys, passwords) in source code. Use `.env` (gitignored) or system environment variables.

---

## Step 4: Verify Installation

```bash
# Check aeronetra package imports correctly
python -c "import aeronetra; print(aeronetra.__version__)"

# Check key dependencies
python -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}')"
python -c "import cv2; print(f'OpenCV: {cv2.__version__}')"
python -c "import ultralytics; print(f'Ultralytics: {ultralytics.__version__}')"

# Run linter and tests
ruff check .
pytest
```

---

## Step 5: GPU Setup (Optional)

If you have an NVIDIA GPU:

1. Install CUDA-compatible PyTorch (check [pytorch.org/get-started](https://pytorch.org/get-started/locally/) for your CUDA version):
   ```bash
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
   ```
2. Verify GPU is available:
   ```bash
   python -c "import torch; print(torch.cuda.get_device_name(0))"
   ```
3. Set `device: "cuda"` in `configs/inference/inference.yaml` (default is `"cpu"`).

---

## Step 6: Kaggle CLI Setup (Optional — for Dataset Downloads)

If using `scripts/download_dataset.py` to download VisDrone from Kaggle:

1. Install Kaggle CLI:
   ```bash
   pip install kaggle
   ```
2. Get your API token from [kaggle.com/settings](https://www.kaggle.com/settings) → "Create New Token"
3. Place `kaggle.json` in:
   - **Windows:** `C:\Users\<username>\.kaggle\kaggle.json`
   - **Linux/Mac:** `~/.kaggle/kaggle.json` (then `chmod 600 ~/.kaggle/kaggle.json`)
4. Test:
   ```bash
   kaggle datasets list -s visdrone
   ```
5. Download using the script (requires explicit `--download` flag):
   ```bash
   python scripts/download_dataset.py --download
   ```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'aeronetra'` | Run `pip install -e .` from the project root |
| `torch.cuda.is_available()` returns `False` | Install CUDA-compatible PyTorch; check NVIDIA driver version |
| `ImportError: libGL.so.1` (Linux) | Install `apt-get install libgl1-mesa-glx` |
| Kaggle `403 Forbidden` | Check `kaggle.json` permissions and API key validity |
