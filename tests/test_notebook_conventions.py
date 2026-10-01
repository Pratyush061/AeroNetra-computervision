import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = REPO_ROOT / "notebooks"


def notebook_code(path: Path) -> str:
    notebook = json.loads(path.read_text(encoding="utf-8"))
    return "\n".join(
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if cell.get("cell_type") == "code"
    )


def test_local_inference_notebooks_require_explicit_weights():
    for notebook_name in (
        "03_yolo26_inference.ipynb",
        "04_yolo11_inference.ipynb",
        "05_yolov8_inference.ipynb",
        "06_rtdetr_inference.ipynb",
    ):
        notebook_path = NOTEBOOK_DIR / notebook_name
        text = notebook_path.read_text(encoding="utf-8")
        code = notebook_code(notebook_path)

        assert "first run will download weights" not in text
        assert "weights_path = model_name" not in code


def test_visdrone_inference_notebooks_use_kaggle_weights_and_all_classes():
    expected = {
        "04_yolo11_inference.ipynb": "yolo11n_visdrone_best.pt",
        "05_yolov8_inference.ipynb": "yolov8n_visdrone_best.pt",
        "06_rtdetr_inference.ipynb": "rtdetr_l_visdrone_best.pt",
    }

    for notebook_name, weight_name in expected.items():
        code = notebook_code(NOTEBOOK_DIR / notebook_name)

        assert f'weights_path = REPO_ROOT / "outputs/models/{weight_name}"' in code
        assert 'class_names = {' in code
        assert '0: "car", 1: "van", 2: "truck", 3: "tricycle"' in code
        assert '7: "bicycle"' in code
        assert "selected_classes = list(range(8))" in code


def test_yolo26_notebook_is_explicit_coco_baseline():
    code = notebook_code(NOTEBOOK_DIR / "03_yolo26_inference.ipynb")

    assert 'weights_path = REPO_ROOT / "outputs/models/yolo26n.pt"' in code
    assert 'class_names = {0: "person", 2: "car", 5: "bus", 7: "truck"}' in code
    assert "selected_classes = [2, 5, 7]" in code


def test_inference_config_declares_all_visdrone_classes():
    config = (REPO_ROOT / "configs/inference/inference.yaml").read_text(encoding="utf-8")

    assert "selected_classes: [0, 1, 2, 3, 4, 5, 6, 7]" in config
