from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    APP_NAME: str = "TraceIQ - Evidence-Grounded Engineering Investigator"
    ENVIRONMENT: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "traceiq_db"
    MONGODB_SOURCE_COLLECTION: str = "sources"
    MONGODB_CHUNK_COLLECTION: str = "chunks"
    MONGODB_VECTOR_INDEX: str = "traceiq_vector_index"

    LLM_PROVIDER: str = "openai"
    OPENAI_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536
    EMBEDDING_BATCH_SIZE: int = 64

    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 120
    RETRIEVAL_CANDIDATE_LIMIT: int = 30
    FINAL_EVIDENCE_LIMIT: int = 10
    REQUEST_TIMEOUT_SECONDS: float = 30.0
    MAX_SOURCE_FILE_BYTES: int = 25 * 1024 * 1024
    DATASET_DIR: str = ""
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    @field_validator("EMBEDDING_DIMENSIONS", "EMBEDDING_BATCH_SIZE", "CHUNK_SIZE",
                     "RETRIEVAL_CANDIDATE_LIMIT", "FINAL_EVIDENCE_LIMIT",
                     "MAX_SOURCE_FILE_BYTES")
    @classmethod
    def positive_integer(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("value must be greater than zero")
        return value

    @field_validator("REQUEST_TIMEOUT_SECONDS")
    @classmethod
    def positive_timeout(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("request timeout must be greater than zero")
        return value

    @model_validator(mode="after")
    def valid_chunk_overlap(self) -> "Settings":
        if self.CHUNK_OVERLAP < 0 or self.CHUNK_OVERLAP >= self.CHUNK_SIZE:
            raise ValueError("CHUNK_OVERLAP must be non-negative and less than CHUNK_SIZE")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def dataset_path(self) -> Path:
        configured = Path(self.DATASET_DIR).expanduser() if self.DATASET_DIR else None
        return (configured if configured and configured.is_absolute()
                else (BACKEND_ROOT / configured if configured else BACKEND_ROOT / "synthetic_data")).resolve()


settings = Settings()
