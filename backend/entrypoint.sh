#!/bin/bash
# Entrypoint script for EchoNote backend container
# Runs database migrations before starting the application

set -e

echo "Running database migrations..."
cd /opt/app-root/src/backend
alembic upgrade head

echo "Starting application..."
cd /opt/app-root/src
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000
