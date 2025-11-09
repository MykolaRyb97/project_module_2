from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class AppConfig(BaseSettings):
    username: str | None = None
    password: str | None = None

    IMAGE_DIR: str
    LOG_DIR: str

    MAX_FILE_SIZE: int = 5 * 1024 * 1024
    SUPPORTED_FORMATS: set[str] = {'.jpg', '.png', '.gif'}

    model_settings = SettingsConfigDict(
        env_file=BASE_DIR / str(".env"),
        enable_decoding="utf-8",
    )


config = AppConfig()