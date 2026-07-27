from aeronetra import config


def test_constants():
    assert config.DEFAULT_CONFIDENCE == 0.5
    assert config.DEFAULT_IOU == 0.45

def test_get_data_dir(monkeypatch):
    monkeypatch.setenv("DATASET_DIR", "/custom/data/path")
    assert str(config.get_data_dir()) == "/custom/data/path"
