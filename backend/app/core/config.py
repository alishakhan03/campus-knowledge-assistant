"""
Central application configuration.

All values are loaded from environment variables (see .env.example).
Nothing here should ever contain a real secret - defaults are for local
development readability only.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    APP_NAME: str = "Campus Knowledge Assistant"

    # --- Database ---
    DATABASE_URL: str = "mysql+pymysql://campus_user:campus_pass@localhost:3306/campus_knowledge"

    # --- Auth ---
    JWT_SECRET_KEY: str = "dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    # --- Pinecone ---
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX_NAME: str = "campus-knowledge"
    PINECONE_NAMESPACE: str = "default"
    PINECONE_CLOUD: str = "aws"
    PINECONE_REGION: str = "us-east-1"

    # --- Gemini ---
    GEMINI_API_KEY: str = ""
    LLM_MODEL: str = "gemini-1.5-flash"
    EMBEDDING_MODEL: str = "models/text-embedding-004"
    EMBEDDING_DIMENSIONS: int = 768

    # --- File storage ---
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 25

    # --- RAG tuning ---
    RAG_TOP_K: int = 5
    RAG_MIN_SCORE: float = 0.70
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 150
    CHAT_HISTORY_TURNS: int = 4

    # --- CORS ---
    FRONTEND_URL: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
