from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Hybrid Search RAG with citation verification"
    app_env: str = "development"
    debug: bool = True

    database_url: str

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "gemini-embedding-2"
    embedding_dimensions: int = 768 
    dense_retrieval_default_top_k: int = 5

    bm25_default_top_k: int = 5
    bm25_k1: float = 1.5
    bm25_b: float = 0.75

    hybrid_default_top_k: int = 5
    hybrid_candidate_k: int = 20
    rrf_k: int = 60

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