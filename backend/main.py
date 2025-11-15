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
from backend.routers import health, transcriptions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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

# Include routers
# Note: Order matters for route matching. More specific routes should come first.

# Health check router (root path)
app.include_router(health.router)

# Authentication router
app.include_router(auth_router)

# Transcription router (main API endpoints)
app.include_router(transcriptions.router)

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
