"""
Routers package for EchoNote API.

This package contains all API routers, organized by domain.
"""

# Expose routers for easy importing
from backend.routers import health, transcriptions

__all__ = ["health", "transcriptions"]
