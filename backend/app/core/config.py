from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Hybrid Search RAG with citation verification"
    app_env: str = "development"
    debug: bool = True

    database_url: str

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    log_level: str = "INFO"

    chunk_target_chars: int = 2800
    chunk_overlap_chars: int = 400

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()