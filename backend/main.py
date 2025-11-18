"""
EchoNote FastAPI Backend

A modern voice transcription API that stores audio recordings and their
transcriptions using Whisper (via vLLM) and SQLModel.

This is the main application entry point. Following best practices,
it uses the lifespan pattern for startup/shutdown and includes modular routers.

Architecture:
- Routers: API endpoint definitions (thin controllers)
- Services: Business logic layer
- Models: Database and API schemas
- Auth: Authentication and authorization
"""

# Configure matplotlib before any imports (defensive measure for diarization)
# This is also set in diarization.py, but setting it here ensures it's
# configured even if matplotlib gets imported indirectly
import os
os.environ['MPLBACKEND'] = 'Agg'
os.environ['MPLCONFIGDIR'] = '/tmp/matplotlib'

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.auth_routes import router as auth_router
from backend.config import settings
from backend.database import create_db_and_tables
from backend.routers import health, transcriptions, actions
from backend.logging_config import setup_logging, get_logger
from backend.middleware.audit_logger import AuditLoggerMiddleware

# Configure enhanced logging
setup_logging(log_dir="backend/logs", log_level=os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger(__name__)


def validate_configuration():
    """
    Validate critical configuration on startup

    Raises:
        RuntimeError: If critical configuration is insecure or invalid
    """
    # Check JWT secret is not default
    default_secrets = [
        "your-secret-key-here",
        "change-me",
        "default",
        "secret",
    ]

    if settings.JWT_SECRET_KEY in default_secrets:
        logger.error("CRITICAL: JWT_SECRET_KEY is using a default/insecure value!")
        logger.error("Set JWT_SECRET_KEY environment variable to a secure random string")
        raise RuntimeError("Insecure JWT configuration - JWT_SECRET_KEY must be changed from default")

    # Check JWT secret strength
    if len(settings.JWT_SECRET_KEY) < 32:
        logger.warning(
            f"JWT_SECRET_KEY is too short ({len(settings.JWT_SECRET_KEY)} characters). "
            f"Recommended: 64+ characters for production security"
        )

    # Create logs directory if it doesn't exist
    os.makedirs("backend/logs", exist_ok=True)

    logger.info("Configuration validation successful")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events using the modern lifespan pattern.
    This replaces the deprecated @app.on_event() decorators.

    Startup:
        - Initialize database tables
        - Log available models

    Shutdown:
        - Clean up resources (if any)

    Args:
        app: FastAPI application instance

    Yields:
        None (application runs between startup and shutdown)
    """
    # ========== Startup ==========
    logger.info("Starting EchoNote API...")

    # Validate critical configuration
    logger.info("Validating configuration...")
    validate_configuration()
    logger.info("Configuration validation passed")

    # Initialize database
    logger.info("Creating database tables...")
    create_db_and_tables()
    logger.info("Database initialized successfully")

    # Log available models
    logger.info(f"Available transcription models: {list(settings.MODELS.keys())}")
    logger.info(f"Default transcription model: {settings.DEFAULT_MODEL}")

    # Log AI assistant models if configured
    if settings.ASSISTANT_MODELS:
        logger.info(f"Available AI assistant models: {list(settings.ASSISTANT_MODELS.keys())}")
        logger.info(f"Default AI assistant model: {settings.DEFAULT_ASSISTANT_MODEL}")
    else:
        logger.info("No AI assistant models configured")

    logger.info("Startup complete - Application ready")

    # ========== Application Running ==========
    yield

    # ========== Shutdown ==========
    logger.info("Shutting down EchoNote API...")
    # Add any cleanup code here if needed
    logger.info("Shutdown complete")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="EchoNote API",
    description="Voice transcription API with audio storage",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add audit logging middleware
app.add_middleware(AuditLoggerMiddleware)

# Include routers
# Note: Order matters for route matching. More specific routes should come first.

# Health check router (root path)
app.include_router(health.router)

# Authentication router
app.include_router(auth_router)

# Transcription router (main API endpoints)
app.include_router(transcriptions.router)

# AI Actions router (AI-powered operations on transcriptions)
app.include_router(actions.router)

logger.info("Routers registered successfully")


# Development server runner
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=True,
    )
