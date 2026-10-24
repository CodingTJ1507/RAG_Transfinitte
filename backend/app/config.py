import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "TraceIQ - Evidence-Grounded Engineering Investigator"
    ENVIRONMENT: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # MongoDB Atlas
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "traceiq_db"
    MONGODB_VECTOR_INDEX: str = "traceiq_vector_index"
    
    # LLM Settings
    OPENAI_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
