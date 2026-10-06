from app.core.config import Settings
from app.scraping import capture


def test_initial_migration_includes_capture_history(tmp_path, monkeypatch):
    from alembic import command
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from sqlalchemy import create_engine, inspect

    config = Config("alembic.ini")
    assert ScriptDirectory.from_config(config).get_heads() == ["initial_schema"]
    engine = create_engine(f"sqlite:///{tmp_path / 'migration.db'}")
    monkeypatch.setattr("app.database.session.engine", engine)
    try:
        command.upgrade(config, "head")
        schema = inspect(engine)
        assert {column["name"] for column in schema.get_columns("page_captures")} == {
            "id",
            "campaign_id",
            "page",
            "created_at",
        }
        assert schema.get_pk_constraint("page_captures")["constrained_columns"] == [
            "id"
        ]
        foreign_key = schema.get_foreign_keys("page_captures")[0]
        assert foreign_key["referred_table"] == "campaigns"
        assert foreign_key["options"]["ondelete"] == "CASCADE"
        assert any(
            index["name"] == "ix_page_captures_campaign_id"
            and index["column_names"] == ["campaign_id"]
            for index in schema.get_indexes("page_captures")
        )
        command.downgrade(config, "base")
        assert set(inspect(engine).get_table_names()) <= {"alembic_version"}
    finally:
        engine.dispose()


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
