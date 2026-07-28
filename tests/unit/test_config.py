from pathlib import Path

from aeronetra import config


def test_constants():
    assert config.DEFAULT_CONFIDENCE == 0.5
    assert config.DEFAULT_IOU == 0.45


def test_directory_paths():
    assert config.DATA_DIR == config.ROOT_DIR / "data"
    assert config.RAW_DATA_DIR == config.DATA_DIR / "raw"
    assert config.PROCESSED_DATA_DIR == config.DATA_DIR / "processed"
    assert config.OUTPUT_DIR == config.ROOT_DIR / "outputs"
    assert config.CONFIGS_DIR == config.ROOT_DIR / "configs"


def test_get_data_dir(monkeypatch):
    monkeypatch.setenv("DATASET_DIR", "/custom/data/path")
    assert str(config.get_data_dir()) == "/custom/data/path"


def test_get_data_dir_default(monkeypatch):
    monkeypatch.delenv("DATASET_DIR", raising=False)
    assert config.get_data_dir() == config.RAW_DATA_DIR


def test_get_output_dir(monkeypatch):
    monkeypatch.setenv("OUTPUT_DIR", "/custom/output")
    assert str(config.get_output_dir()) == "/custom/output"


def test_load_yaml():
    cfg = config.load_yaml(config.CONFIGS_DIR / "inference" / "inference.yaml")
    assert "confidence_threshold" in cfg
    assert "iou_threshold" in cfg
    assert cfg["confidence_threshold"] == 0.25
    assert cfg["iou_threshold"] == 0.45


def test_load_yaml_missing():
    import pytest
    with pytest.raises(FileNotFoundError):
        config.load_yaml(Path("/nonexistent/config.yaml"))


def test_load_inference_config():
    cfg = config.load_inference_config()
    assert cfg["image_size"] == [640, 640]
    assert cfg["max_detections"] == 300
