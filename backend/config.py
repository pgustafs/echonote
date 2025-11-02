"""
Application configuration settings.

Environment variables:
- MODEL_URL: URL of the vLLM Whisper server
- MODEL_NAME: Name of the Whisper model to use
- API_KEY: API key for vLLM server
- DATABASE_URL: PostgreSQL connection string (production)
- SQLITE_DB: SQLite database filename (development, default: echonote.db)
- DB_ECHO: Enable SQL query logging (default: false)
- BACKEND_PORT: Port for FastAPI server (default: 8000)
- BACKEND_HOST: Host for FastAPI server (default: 0.0.0.0)
- CORS_ORIGINS: Comma-separated list of allowed CORS origins
"""

import os
from typing import List


class Settings:
    """Application settings loaded from environment variables."""

    # Whisper/vLLM Configuration
    MODEL_URL: str = os.getenv(
        "MODEL_URL",
        "https://whisper-large-v3-turbo-quantizedw4a16-models.apps.ai3.pgustafs.com/v1"
    )
    MODEL_NAME: str = os.getenv(
        "MODEL_NAME",
        "whisper-large-v3-turbo-quantizedw4a16"
    )
    API_KEY: str = os.getenv("API_KEY", "EMPTY")

    # Server Configuration
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")

    # CORS Configuration
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:3000"
    ).split(",")

    # Database Configuration (handled in database.py)
    # File Upload Configuration
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", str(50 * 1024 * 1024)))  # 50MB default
    ALLOWED_AUDIO_TYPES: List[str] = [
        "audio/wav",
        "audio/wave",
        "audio/x-wav",
        "audio/mpeg",
        "audio/mp3",
        "audio/webm",
        "audio/ogg",
        "audio/flac",
    ]


settings = Settings()
