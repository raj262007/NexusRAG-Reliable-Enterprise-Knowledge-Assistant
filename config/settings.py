import os
from pathlib import Path
from typing import List
from pydantic import BaseModel, Field


def load_env_file(dotenv_path: Path):
    """Simple, dependency-free .env file parser."""
    if not dotenv_path.is_file():
        return
    try:
        with open(dotenv_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                if key and key not in os.environ:
                    os.environ[key] = val
    except Exception:
        pass


# Automatically load .env from project root if present
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_env_file(_PROJECT_ROOT / ".env")


class Settings(BaseModel):
    PROJECT_NAME: str = Field(
        default_factory=lambda: os.getenv("PROJECT_NAME", "NexusRAG")
    )
    ENVIRONMENT: str = Field(
        default_factory=lambda: os.getenv("ENVIRONMENT", "development")
    )
    BASE_DIR: Path = Field(default=_PROJECT_ROOT)
    UPLOAD_DIR: Path = Field(
        default_factory=lambda: _PROJECT_ROOT / os.getenv("UPLOAD_DIR", "data/uploads")
    )
    PROCESSED_DIR: Path = Field(
        default_factory=lambda: _PROJECT_ROOT / os.getenv("PROCESSED_DIR", "data/processed")
    )
    QDRANT_STORAGE_PATH: Path = Field(
        default_factory=lambda: _PROJECT_ROOT / os.getenv("QDRANT_STORAGE_PATH", "data/qdrant")
    )
    COLLECTION_NAME: str = Field(
        default_factory=lambda: os.getenv("COLLECTION_NAME", "nexusrag")
    )
    EMBEDDING_MODEL: str = Field(
        default_factory=lambda: os.getenv(
            "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        )
    )
    EMBEDDING_DEVICE: str = Field(
        default_factory=lambda: os.getenv("EMBEDDING_DEVICE", "cpu")
    )
    CHUNK_SIZE: int = Field(
        default_factory=lambda: int(os.getenv("CHUNK_SIZE", "500"))
    )
    CHUNK_OVERLAP: int = Field(
        default_factory=lambda: int(os.getenv("CHUNK_OVERLAP", "100"))
    )
    MAX_FILE_SIZE_MB: int = Field(
        default_factory=lambda: int(os.getenv("MAX_FILE_SIZE_MB", "25"))
    )
    ALLOWED_EXTENSIONS: List[str] = Field(
        default_factory=lambda: [".pdf", ".docx", ".csv"]
    )
    OLLAMA_BASE_URL: str = Field(
        default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    )
    OLLAMA_MODEL: str = Field(
        default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
    )
    OLLAMA_TIMEOUT_SECONDS: float = Field(
        default_factory=lambda: float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "60.0"))
    )
    TOP_K_RETRIEVAL: int = Field(
        default_factory=lambda: int(os.getenv("TOP_K_RETRIEVAL", "5"))
    )
    RRF_K: int = Field(
        default_factory=lambda: int(os.getenv("RRF_K", "60"))
    )
    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ]
    )


settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
settings.QDRANT_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
