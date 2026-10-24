import json
import math
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

    APP_NAME: str = "Concord.ai - Evidence-Grounded Engineering Investigator"
    ENVIRONMENT: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "traceiq_db"
    MONGODB_SOURCE_COLLECTION: str = "sources"
    MONGODB_CHUNK_COLLECTION: str = "chunks"
    MONGODB_VECTOR_INDEX: str = "traceiq_vector_index"
    MONGODB_SEARCH_INDEX: str = "traceiq_search_index"

    GEMINI_API_KEY: str = ""
    LLM_MODEL: str = "gemini-2.5-flash"
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    EMBEDDING_DIMENSIONS: int = 768
    EMBEDDING_BATCH_SIZE: int = 64

    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 60
    RETRIEVAL_CANDIDATE_LIMIT: int = 30
    FINAL_EVIDENCE_LIMIT: int = 10
    REQUEST_TIMEOUT_SECONDS: float = 30.0
    SEARCH_INDEX_TIMEOUT_SECONDS: float = 90.0  # below the frontend's 120 s request timeout
    MAX_SOURCE_FILE_BYTES: int = 25 * 1024 * 1024
    DATASET_DIR: str = ""
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    SERVICE_OWNERS: str = '{"payment-service": "Payments Team", "order-service": "Orders Team"}'

    @field_validator("EMBEDDING_DIMENSIONS", "EMBEDDING_BATCH_SIZE", "CHUNK_SIZE",
                     "RETRIEVAL_CANDIDATE_LIMIT", "FINAL_EVIDENCE_LIMIT",
                     "MAX_SOURCE_FILE_BYTES")
    @classmethod
    def positive_integer(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("value must be greater than zero")
        return value

    @field_validator("REQUEST_TIMEOUT_SECONDS", "SEARCH_INDEX_TIMEOUT_SECONDS")
    @classmethod
    def positive_timeout(cls, value: float) -> float:
        if not math.isfinite(value) or value <= 0:
            raise ValueError("timeout must be a finite number greater than zero")
        return value

    @field_validator("SERVICE_OWNERS")
    @classmethod
    def valid_service_owners(cls, value: str) -> str:
        try:
            service_owners = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("SERVICE_OWNERS must be a JSON object of strings") from exc
        if not isinstance(service_owners, dict) or any(
            not isinstance(service, str) or not isinstance(owner, str)
            for service, owner in service_owners.items()
        ):
            raise ValueError("SERVICE_OWNERS must be a JSON object of strings")
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
    def service_owner_map(self) -> dict[str, str]:
        return json.loads(self.SERVICE_OWNERS)

    @property
    def dataset_path(self) -> Path:
        configured = Path(self.DATASET_DIR).expanduser() if self.DATASET_DIR else None
        return (configured if configured and configured.is_absolute()
                else (BACKEND_ROOT / configured if configured else BACKEND_ROOT / "synthetic_data")).resolve()


settings = Settings()
