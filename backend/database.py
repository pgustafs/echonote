"""
Database configuration and session management.

Supports both SQLite (development) and PostgreSQL (production)
based on environment configuration.
"""

import os
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine


def get_database_url() -> str:
    """
    Get database URL based on environment.

    Returns:
        Database URL string for SQLite or PostgreSQL
    """
    # Check if PostgreSQL URL is provided (production)
    postgres_url = os.getenv("DATABASE_URL")
    if postgres_url:
        # Handle Railway/Render postgres:// -> postgresql:// conversion
        if postgres_url.startswith("postgres://"):
            postgres_url = postgres_url.replace("postgres://", "postgresql://", 1)
        return postgres_url

    # Check if individual PostgreSQL credentials are provided (e.g., Kubernetes)
    pg_user = os.getenv("POSTGRESQL_USER")
    pg_password = os.getenv("POSTGRESQL_PASSWORD")
    pg_database = os.getenv("POSTGRESQL_DATABASE")
    pg_host = os.getenv("POSTGRESQL_HOST", "postgresql")
    pg_port = os.getenv("POSTGRESQL_PORT", "5432")

    if pg_user and pg_password and pg_database:
        return f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"

    # Default to SQLite (development)
    db_file = os.getenv("SQLITE_DB", "echonote.db")
    return f"sqlite:///{db_file}"


# Database engine configuration
database_url = get_database_url()

# SQLite-specific connection arguments
connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}

# Create engine with echo for debugging (disable in production)
engine = create_engine(
    database_url,
    echo=os.getenv("DB_ECHO", "false").lower() == "true",
    connect_args=connect_args
)


def create_db_and_tables():
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.

    Yields:
        Database session for use in FastAPI endpoints
    """
    with Session(engine) as session:
        yield session
