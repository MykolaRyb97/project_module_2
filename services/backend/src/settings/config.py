from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[4]


class AppConfig(BaseSettings):
    username: str | None = None
    password: str | None = None

    IMAGE_DIR: Path
    LOG_DIR: Path
    WEB_SERVER_WORKERS: int
    WEB_SERVER_START_PORT: int

    MAX_FILE_SIZE: int = 5 * 1024 * 1024
    SUPPORTED_FORMATS: set[str] = {'.jpg', '.png', '.gif'}

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
    )


config = AppConfig()
