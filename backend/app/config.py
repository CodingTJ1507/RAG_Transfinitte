import os
from typing import List, Union
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
    
    # Provider Selection: "gemini" or "openai"
    LLM_PROVIDER: str = "gemini"
    
    # Google Gemini Settings (Free Tier)
    GEMINI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    
    # OpenAI Settings (Fallback / Alternative)
    OPENAI_API_KEY: str = ""
    
    # Model Configurations
    LLM_MODEL: str = "gemini-3.1-flash-lite"
    EMBEDDING_MODEL: str = "models/gemini-embedding-001"
    EMBEDDING_DIMENSIONS: int = 3072
    
    # CORS (Stored as string to prevent JSON parsing issues with comma-separated env values)
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        val = self.CORS_ORIGINS
        if isinstance(val, list):
            return val
        if val.startswith('[') and val.endswith(']'):
            import json
            try:
                return json.loads(val)
            except Exception:
                pass
        return [i.strip() for i in val.split(',') if i.strip()]

    def get_google_api_key(self) -> str:
        """Returns the configured Gemini/Google API key."""
        return self.GEMINI_API_KEY or self.GOOGLE_API_KEY or os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
