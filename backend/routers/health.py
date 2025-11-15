"""
Health Check API Router

This module provides simple health check endpoints for monitoring
application status and readiness.
"""

from fastapi import APIRouter

# Create router
router = APIRouter(
    tags=["health"],
)


@router.get("/")
def health_check():
    """
    Basic health check endpoint.

    Returns application name, status, and version information.
    Useful for uptime monitoring and load balancer health checks.

    No authentication required.

    Returns:
        dict: Application health status information
    """
    return {
        "app": "EchoNote API",
        "status": "healthy",
        "version": "1.0.0"
    }
