"""
Audit Logging Middleware

Automatically logs all authenticated API requests for security and compliance.
"""

import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from backend.logging_config import get_security_logger
import json

logger = get_security_logger()


class AuditLoggerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all API requests for audit trail
    """

    # Paths to exclude from audit logging
    EXCLUDED_PATHS = [
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/favicon.ico",
    ]

    # Sensitive fields to sanitize in logs
    SENSITIVE_FIELDS = [
        "password",
        "token",
        "access_token",
        "refresh_token",
        "api_key",
        "secret",
    ]

    async def dispatch(self, request: Request, call_next):
        """
        Process request and log audit information

        Args:
            request: FastAPI Request object
            call_next: Next middleware/handler in chain

        Returns:
            Response from next handler
        """
        # Skip excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        # Record start time
        start_time = time.time()

        # Extract user information if available
        user_id = None
        username = None

        try:
            # Try to extract user from request state (set by auth dependency)
            if hasattr(request.state, "user"):
                user = request.state.user
                user_id = getattr(user, "id", None)
                username = getattr(user, "username", None)
        except Exception:
            # User not authenticated or error extracting user
            pass

        # Extract client information
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        # Extract query parameters (sanitized)
        query_params = dict(request.query_params)
        query_params = self._sanitize_dict(query_params)

        # Process request
        error = None
        status_code = 500

        try:
            response: Response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            error = str(e)
            raise
        finally:
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log audit entry
            log_data = {
                "user_id": user_id,
                "username": username,
                "method": request.method,
                "path": request.url.path,
                "query_params": query_params,
                "ip_address": client_ip,
                "user_agent": user_agent,
                "status_code": status_code,
                "duration_ms": duration_ms,
            }

            if error:
                log_data["error"] = error

            # Log at appropriate level based on status code
            if status_code >= 500:
                logger.error(f"Request failed: {request.method} {request.url.path}", extra=log_data)
            elif status_code >= 400:
                logger.warning(f"Request error: {request.method} {request.url.path}", extra=log_data)
            else:
                # Only log successful authenticated requests at INFO level
                if user_id:
                    logger.info(f"Request: {request.method} {request.url.path}", extra=log_data)

        return response

    @staticmethod
    def _sanitize_dict(data: dict) -> dict:
        """
        Remove sensitive values from dictionary

        Args:
            data: Dictionary to sanitize

        Returns:
            Sanitized dictionary
        """
        sanitized = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in AuditLoggerMiddleware.SENSITIVE_FIELDS):
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value
        return sanitized
