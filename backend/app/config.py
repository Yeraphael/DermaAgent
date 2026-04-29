from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]


class Settings(BaseSettings):
    app_name: str = "肤联智诊 API"
    base_url: str = "http://127.0.0.1:8000"
    api_prefix: str = "/api/v1"
    jwt_secret: str = "replace-with-a-long-random-secret"
    jwt_expire_minutes: int = 720

    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = "123456"
    mysql_database: str = "derma_agent"
    mysql_charset: str = "utf8mb4"

    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:5174,http://localhost:5174"
    upload_dir: str = "backend/uploads"

    ai_mode: str = "mock"
    qwen_api_key: str | None = None
    qwen_base_url: str | None = None
    qwen_visual_model: str = "qwen-vl-plus"
    qwen_text_model: str = "qwen-plus"
    text_qa_model: str = "qwen-plus"
    tavily_api_key: str | None = None
    tavily_enabled: bool = False
    chat_history_limit: int = 10
    chat_temperature: float = 0.2
    chat_max_tokens: int = 1200
    chat_timeout_seconds: int = 30

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset={self.mysql_charset}"
        )

    @property
    def upload_path(self) -> Path:
        return PROJECT_ROOT / self.upload_dir

    @property
    def parsed_cors_origins(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    return settings
