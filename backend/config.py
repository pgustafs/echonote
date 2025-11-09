"""
Application configuration settings.

Environment variables:
- MODELS: JSON object mapping model names to base URLs
  Example: '{"whisper-large-v3-turbo": "https://...", "whisper-medium": "https://..."}'
- DEFAULT_MODEL: Name of the default model (must be a key in MODELS)
- API_KEY: API key for vLLM server
- DATABASE_URL: PostgreSQL connection string (production)
- SQLITE_DB: SQLite database filename (development, default: echonote.db)
- DB_ECHO: Enable SQL query logging (default: false)
- BACKEND_PORT: Port for FastAPI server (default: 8000)
- BACKEND_HOST: Host for FastAPI server (default: 0.0.0.0)
- CORS_ORIGINS: Comma-separated list of allowed CORS origins
- DIARIZATION_MODEL: Pyannote model for speaker diarization (default: pyannote/speaker-diarization-3.1)
- HF_TOKEN: Hugging Face token for accessing gated models

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
        """Load model configurations from environment variables."""
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

    MODELS: Dict[str, str] = None  # Will be set in __init__
    DEFAULT_MODEL: str = None  # Will be set in __init__
    API_KEY: str = os.getenv("API_KEY", "EMPTY")

    def __init__(self):
        """Initialize settings and load models."""
        self.MODELS = self._load_models()

        # Set default model
        default_from_env = os.getenv("DEFAULT_MODEL")
        if default_from_env and default_from_env in self.MODELS:
            self.DEFAULT_MODEL = default_from_env
        else:
            # Use the first model as default
            self.DEFAULT_MODEL = list(self.MODELS.keys())[0]

    def get_model_url(self, model_name: str) -> str:
        """Get the base URL for a specific model."""
        if model_name not in self.MODELS:
            raise ValueError(f"Unknown model: {model_name}. Available models: {list(self.MODELS.keys())}")
        return self.MODELS[model_name]

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

    # Speaker Diarization Configuration
    DIARIZATION_MODEL: str = os.getenv(
        "DIARIZATION_MODEL",
        "pyannote/speaker-diarization-3.1"
    )
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")  # Hugging Face token for gated models


settings = Settings()
