from app.core.config import Settings
from app.scraping import capture


def test_one_database_setting():
    settings = Settings(_env_file=None, database_url="sqlite:///research.db")
    assert settings.database_url == "sqlite:///research.db"
    assert "data_mode" not in Settings.model_fields
    assert "demo_database_url" not in Settings.model_fields


def test_capture_paths_preserve_existing_files(tmp_path, monkeypatch):
    monkeypatch.setattr(capture, "ROOT", tmp_path)
    identity = "39b5bfb3-9860-43c6-96e6-f9aa3550c018"
    previous = tmp_path / "old_namespace" / identity / "dom.json"
    previous.parent.mkdir(parents=True)
    previous.write_text('{"html": "saved evidence"}')
    assert capture.artifact_path(identity, "dom.json") == previous
    current = tmp_path / identity / "dom.json"
    current.parent.mkdir()
    current.write_text('{"html": "new evidence"}')
    assert capture.artifact_path(identity, "dom.json") == current
    assert previous.read_text() == '{"html": "saved evidence"}'
