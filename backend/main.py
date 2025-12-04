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
from slowapi.errors import RateLimitExceeded

from backend.auth_routes import router as auth_router
from backend.config import settings
from backend.database import create_db_and_tables
from backend.routers import health, transcriptions, actions, admin, saved_content
from backend.logging_config import setup_logging, get_logger
from backend.middleware.audit_logger import AuditLoggerMiddleware
from backend.middleware.rate_limiter import limiter, rate_limit_exceeded_handler

# Configure enhanced logging
setup_logging(log_dir="backend/logs", log_level=os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger(__name__)


def validate_configuration():
    """
    Validate critical configuration on startup

    Phase 4: Security Hardening - Enhanced configuration validation

    Raises:
        RuntimeError: If critical configuration is insecure or invalid
    """
    errors = []
    warnings = []

    # ===== JWT Security Validation =====

    # Check JWT secret is not default
    default_secrets = [
        "your-secret-key-here",
        "your-secret-key-change-this-in-production",  # Phase 4.1: Security fix
        "change-me",
        "default",
        "secret",
        "CHANGE_THIS_TO_SECURE_RANDOM_STRING_MINIMUM_64_CHARACTERS_IN_PRODUCTION",
        "CHANGE_THIS_TO_SECURE_RANDOM_STRING_IN_PRODUCTION",
    ]

    if settings.JWT_SECRET_KEY in default_secrets:
        errors.append(
            "JWT_SECRET_KEY is using a default/insecure value! "
            "Generate a secure key with: python3 -c \"import secrets; print(secrets.token_urlsafe(64))\""
        )

    # Check JWT secret strength
    if len(settings.JWT_SECRET_KEY) < 32:
        warnings.append(
            f"JWT_SECRET_KEY is too short ({len(settings.JWT_SECRET_KEY)} characters). "
            f"Recommended: 64+ characters for production security"
        )
    elif len(settings.JWT_SECRET_KEY) < 64:
        warnings.append(
            f"JWT_SECRET_KEY could be stronger ({len(settings.JWT_SECRET_KEY)} characters). "
            f"Recommended: 64+ characters"
        )

    # ===== CORS Validation =====

    # Check CORS origins
    if "*" in settings.CORS_ORIGINS:
        warnings.append(
            "CORS_ORIGINS includes '*' which allows all origins. "
            "This should only be used in development, not production!"
        )

    # Check if running with production database
    database_url = os.getenv("DATABASE_URL", "")
    sqlite_db = os.getenv("SQLITE_DB", "")

    if sqlite_db and not database_url:
        warnings.append(
            "Using SQLite database. "
            "For production, please use PostgreSQL (set DATABASE_URL environment variable)"
        )

    # ===== File System Checks =====

    # Create logs directory if it doesn't exist
    logs_dir = os.path.join("backend", "logs")
    try:
        os.makedirs(logs_dir, exist_ok=True)
        # Test write permissions
        test_file = os.path.join(logs_dir, ".write_test")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
    except Exception as e:
        errors.append(f"Cannot write to logs directory: {e}")

    # Create data directory if it doesn't exist
    data_dir = "data"
    try:
        os.makedirs(data_dir, exist_ok=True)
    except Exception as e:
        warnings.append(f"Cannot create data directory: {e}")

    # ===== Environment Validation =====

    # Check if running in development mode (DEBUG)
    if os.getenv("DEBUG", "").lower() in ["true", "1", "yes"]:
        warnings.append("DEBUG mode is enabled. Disable in production!")

    # Check log level
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    if log_level == "DEBUG":
        warnings.append("LOG_LEVEL is set to DEBUG. Use INFO or WARNING in production.")

    # ===== Report Results =====

    if errors:
        logger.error("=" * 70)
        logger.error("CONFIGURATION VALIDATION FAILED")
        logger.error("=" * 70)
        for error in errors:
            logger.error(f"ERROR: {error}")
        logger.error("=" * 70)
        logger.error("Application cannot start with these configuration errors!")
        logger.error("=" * 70)
        raise RuntimeError(f"Configuration validation failed: {len(errors)} error(s) found")

    if warnings:
        logger.warning("=" * 70)
        logger.warning("CONFIGURATION WARNINGS")
        logger.warning("=" * 70)
        for warning in warnings:
            logger.warning(f"WARNING: {warning}")
        logger.warning("=" * 70)
        logger.warning("Application starting despite warnings. Review configuration for production.")
        logger.warning("=" * 70)

    logger.info("Configuration validation completed successfully")


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

# Configure rate limiting
# Phase 4: Security Hardening - Add rate limiting to prevent abuse
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

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

# Saved Content router (saved AI-generated content)
app.include_router(saved_content.router)

# AI Actions router (AI-powered operations on transcriptions)
app.include_router(actions.router)

# Admin router (administrative endpoints for user/system management)
app.include_router(admin.router)

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
