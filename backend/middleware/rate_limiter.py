"""
Rate limiting middleware for EchoNote API.

Phase 4: Security Hardening - Rate limiting to prevent abuse

Uses slowapi (Flask-Limiter for FastAPI) with Redis backend for
distributed rate limiting across multiple application instances.

Rate Limits:
- Authentication endpoints: 5 attempts per 15 minutes per IP
- Registration: 3 attempts per hour per IP
- Transcription endpoints: 10 requests per minute per user
- AI action endpoints: 30 requests per minute per user
"""

import os
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from backend.config import settings


def get_user_identifier(request: Request) -> str:
    """
    Get user identifier for rate limiting.

    For authenticated requests, uses user ID from token.
    For unauthenticated requests, uses IP address.

    Args:
        request: FastAPI request object

    Returns:
        User identifier string for rate limiting
    """
    # Try to get user from request state (set by auth middleware)
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"

    # Fall back to IP address for unauthenticated requests
    return f"ip:{get_remote_address(request)}"


# Initialize rate limiter with Redis backend
# Use database 2 to avoid conflicts with Celery (db 0 and 1) and token blacklist (db 3)
rate_limit_redis_url = settings.REDIS_URL.rsplit('/', 1)[0] + '/2'
limiter = Limiter(
    key_func=get_user_identifier,
    storage_uri=rate_limit_redis_url,
    default_limits=[os.getenv("DEFAULT_RATE_LIMIT", "100/minute")],
    headers_enabled=True,  # Include rate limit info in response headers
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors.

    Returns a JSON response with rate limit information instead of plain text.

    Args:
        request: The request that triggered the rate limit
        exc: The RateLimitExceeded exception

    Returns:
        JSON response with 429 status code
    """
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded",
            "message": str(exc.detail),
            "retry_after": getattr(exc, "retry_after", None),
        },
        headers={
            "Retry-After": str(getattr(exc, "retry_after", 60)),
        },
    )


# Rate limit decorators for different endpoint types

def auth_rate_limit():
    """
    Rate limit for authentication endpoints (login).

    Limit: 5 attempts per 15 minutes per IP address
    """
    return limiter.limit("5/15minutes", key_func=lambda request: f"ip:{get_remote_address(request)}")


def registration_rate_limit():
    """
    Rate limit for user registration.

    Limit: 3 attempts per hour per IP address
    """
    return limiter.limit("3/hour", key_func=lambda request: f"ip:{get_remote_address(request)}")


def transcription_rate_limit():
    """
    Rate limit for transcription endpoints.

    Limit: 10 requests per minute per user
    """
    return limiter.limit("10/minute")


def ai_action_rate_limit():
    """
    Rate limit for AI action endpoints.

    Limit: 30 requests per minute per user
    """
    return limiter.limit("30/minute")
