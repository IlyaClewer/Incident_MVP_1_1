from functools import lru_cache
from pathlib import Path

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BASE_DIR = PROJECT_ROOT.parent / "incident_secret"
ENV_FILE = BASE_DIR / ".env"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "incidence-backend"
    APP_ENV: str = "dev"
    DEBUG: bool = False

    ISBP_BASE_URL: str = "https://test-aipss.cito-priorov.ru"
    ISBP_STATIC_TOKEN: str | None = None
    ISBP_CREATE_PATH: str = "/vbo/create_from_incidents"
    ISBP_STATUS_PATH: str = "/vbo/incidents/status"
    ISBP_TIMEOUT_SECONDS: int = 15
    ISBP_POLL_LIMIT: int = 100

    DB_HOST: str
    DB_PORT: int = 5432
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_PASSWORD_Alembic: str
    DB_SCHEMA_PUBLIC: str = "public"
    DB_SCHEMA_REMOTE: str = "remote"
    DB_ECHO: bool
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 1800

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
    @computed_field
    @property
    def DATABASE_URL_SYNC(self) -> str:
        return (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD_Alembic}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
