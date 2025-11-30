"""
Application configuration settings.

Environment variables:
- MODELS: JSON object mapping model names to base URLs
  Example: '{"whisper-large-v3-turbo": "https://...", "whisper-medium": "https://..."}'
- DEFAULT_MODEL: Name of the default model (must be a key in MODELS)
- API_KEY: API key for vLLM server
- ASSISTANT_MODELS: JSON object mapping AI assistant model names to base URLs
  Example: '{"llama-3.1-70b": "https://...", "qwen-2.5-72b": "https://..."}'
- DEFAULT_ASSISTANT_MODEL: Name of the default AI assistant model (must be a key in ASSISTANT_MODELS)
- ASSISTANT_API_KEY: API key for AI assistant vLLM server (defaults to API_KEY if not set)
- DATABASE_URL: PostgreSQL connection string (production)
- SQLITE_DB: SQLite database filename (development, default: echonote.db)
- DB_ECHO: Enable SQL query logging (default: false)
- APP_PORT: Port for FastAPI server (default: 8000)
- APP_HOST: Host for FastAPI server (default: 0.0.0.0)
- CORS_ORIGINS: Comma-separated list of allowed CORS origins
- DIARIZATION_MODEL: Pyannote model for speaker diarization (default: pyannote/speaker-diarization-3.1)
- HF_TOKEN: Hugging Face token for accessing gated models
- DEFAULT_PAGE_SIZE: Default number of transcriptions per page (default: 10)
- MAX_PAGE_SIZE: Maximum allowed page size (default: 100)
- MINIO_ENDPOINT: MinIO server endpoint (default: minio:9000)
- MINIO_ACCESS_KEY: MinIO access key (default: minioadmin)
- MINIO_SECRET_KEY: MinIO secret key (default: minioadmin123)
- MINIO_BUCKET: MinIO bucket name for audio files (default: echonote-audio)
- MINIO_SECURE: Use HTTPS for MinIO connection (default: false)

Legacy environment variables (deprecated, use MODELS instead):
- MODEL_URL: URL of the vLLM Whisper server
- MODEL_NAME: Name of the Whisper model to use
"""

import json
import os
from typing import Dict, List


class Settings:
    """Application settings loaded from environment variables."""

    # Whisper/vLLM Configuration
    # Support both new MODELS format and legacy MODEL_URL/MODEL_NAME
    def _load_models(self) -> Dict[str, str]:
        """Load transcription model configurations from environment variables."""
        models_json = os.getenv("MODELS")

        if models_json:
            try:
                return json.loads(models_json)
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse MODELS env var: {e}")
                print("Falling back to legacy MODEL_URL/MODEL_NAME")

        # Fallback to legacy single model configuration
        model_name = os.getenv(
            "MODEL_NAME",
            "whisper-large-v3-turbo-quantizedw4a16"
        )
        model_url = os.getenv(
            "MODEL_URL",
            "https://whisper-large-v3-turbo-quantizedw4a16-models.apps.ai3.pgustafs.com/v1"
        )
        return {model_name: model_url}

    def _load_assistant_models(self) -> Dict[str, str]:
        """Load AI assistant model configurations from environment variables."""
        models_json = os.getenv("ASSISTANT_MODELS")

        if models_json:
            try:
                return json.loads(models_json)
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse ASSISTANT_MODELS env var: {e}")
                return {}

        # Return empty dict if not configured (assistant models are optional)
        return {}

    MODELS: Dict[str, str] = None  # Will be set in __init__
    DEFAULT_MODEL: str = None  # Will be set in __init__
    API_KEY: str = os.getenv("API_KEY", "EMPTY")

    ASSISTANT_MODELS: Dict[str, str] = None  # Will be set in __init__
    DEFAULT_ASSISTANT_MODEL: str = None  # Will be set in __init__
    ASSISTANT_API_KEY: str = None  # Will be set in __init__

    def __init__(self):
        """Initialize settings and load models."""
        # Load transcription models
        self.MODELS = self._load_models()

        # Set default transcription model
        default_from_env = os.getenv("DEFAULT_MODEL")
        if default_from_env and default_from_env in self.MODELS:
            self.DEFAULT_MODEL = default_from_env
        else:
            # Use the first model as default
            self.DEFAULT_MODEL = list(self.MODELS.keys())[0]

        # Load AI assistant models
        self.ASSISTANT_MODELS = self._load_assistant_models()

        # Set default assistant model
        if self.ASSISTANT_MODELS:
            default_assistant_from_env = os.getenv("DEFAULT_ASSISTANT_MODEL")
            if default_assistant_from_env and default_assistant_from_env in self.ASSISTANT_MODELS:
                self.DEFAULT_ASSISTANT_MODEL = default_assistant_from_env
            else:
                # Use the first assistant model as default
                self.DEFAULT_ASSISTANT_MODEL = list(self.ASSISTANT_MODELS.keys())[0]
        else:
            self.DEFAULT_ASSISTANT_MODEL = None

        # Set assistant API key (defaults to main API_KEY if not specified)
        self.ASSISTANT_API_KEY = os.getenv("ASSISTANT_API_KEY", self.API_KEY)

    def get_model_url(self, model_name: str) -> str:
        """Get the base URL for a specific transcription model."""
        if model_name not in self.MODELS:
            raise ValueError(f"Unknown model: {model_name}. Available models: {list(self.MODELS.keys())}")
        return self.MODELS[model_name]

    def get_assistant_model_url(self, model_name: str) -> str:
        """Get the base URL for a specific AI assistant model."""
        if not self.ASSISTANT_MODELS:
            raise ValueError("No AI assistant models configured")
        if model_name not in self.ASSISTANT_MODELS:
            raise ValueError(f"Unknown assistant model: {model_name}. Available models: {list(self.ASSISTANT_MODELS.keys())}")
        return self.ASSISTANT_MODELS[model_name]

    # Server Configuration
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")

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

    # Speaker Diarization Configuration
    DIARIZATION_MODEL: str = os.getenv(
        "DIARIZATION_MODEL",
        "pyannote/speaker-diarization-3.1"
    )
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")  # Hugging Face token for gated models

    # Pagination Configuration
    DEFAULT_PAGE_SIZE: int = int(os.getenv("DEFAULT_PAGE_SIZE", "10"))
    MAX_PAGE_SIZE: int = int(os.getenv("MAX_PAGE_SIZE", "100"))

    # JWT Authentication Configuration
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY",
        "your-secret-key-change-this-in-production"  # MUST be changed in production
    )
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

    # Phase 4.1: Security fix - Shorter access token lifetime
    # Access tokens now default to 15 minutes for better security
    # Use refresh tokens for longer sessions
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))

    # Refresh token lifetime (7 days default)
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # Legacy support - if ACCESS_TOKEN_EXPIRE_DAYS is set, use it (in minutes)
    # This maintains backward compatibility
    if os.getenv("ACCESS_TOKEN_EXPIRE_DAYS"):
        legacy_days = int(os.getenv("ACCESS_TOKEN_EXPIRE_DAYS"))
        ACCESS_TOKEN_EXPIRE_MINUTES = legacy_days * 24 * 60

    # Redis and Celery Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

    # MinIO Object Storage Configuration
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "minio:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
    MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "echonote-audio")
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"

    # Audio Chunking Configuration
    CHUNK_DURATION_SECONDS: int = int(os.getenv("CHUNK_DURATION_SECONDS", "60"))  # 60-second chunks
    MAX_AUDIO_DURATION_SECONDS: int = int(os.getenv("MAX_AUDIO_DURATION_SECONDS", "3600"))  # 1 hour max

    # LlamaStack Configuration (AI Actions)
    LLAMA_SERVER_URL: str = os.getenv("LLAMA_SERVER_URL", "")
    LLAMA_MODEL_NAME: str = os.getenv("LLAMA_MODEL_NAME", "")
    LLAMA_STACK_CLIENT_API_KEY: str = os.getenv("LLAMA_STACK_CLIENT_API_KEY", "fake")


settings = Settings()
