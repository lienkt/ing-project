from typing import Literal
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    data_mode: Literal["real", "demo"] = "real"
    database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/campaign_db"
    )
    demo_database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/campaign_demo_db"
    )
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ]
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def separate_databases(self):
        def identity(value):
            url = make_url(value)
            host = (
                "localhost"
                if url.host in ("localhost", "127.0.0.1", "::1")
                else url.host
            )
            return (host, url.port or 5432, url.database)

        if identity(self.database_url) == identity(self.demo_database_url):
            raise ValueError(
                "DATABASE_URL and DEMO_DATABASE_URL must identify separate databases."
            )
        return self

    @property
    def active_database_url(self) -> str:
        return self.demo_database_url if self.data_mode == "demo" else self.database_url


settings = Settings()
