from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    auth_enabled: bool = False
    oidc_issuer: str = ""
    oidc_audience: str = "banking-api"
    database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/campaign_db"
    )
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ]
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
