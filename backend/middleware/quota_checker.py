"""
Quota Checker Middleware and Decorators

Provides decorators for checking user quotas and roles on API endpoints.
"""

from functools import wraps
from typing import Callable
from fastapi import HTTPException, status
from backend.models import User
from backend.services.permission_service import PermissionService
from backend.logging_config import get_security_logger

security_logger = get_security_logger()


def require_quota(cost: int = 1):
    """
    Decorator to require sufficient user quota for endpoint access

    Args:
        cost: Number of quota units required (default: 1)

    Raises:
        HTTPException: 429 if quota exceeded

    Example:
        @router.post("/actions/analyze")
        @require_quota(cost=1)
        async def analyze(user: User = Depends(get_current_user)):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs (injected by Depends(get_current_user))
            user = kwargs.get('user') or kwargs.get('current_user')

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            # Check quota
            if not PermissionService.check_user_quota(user, cost):
                usage_stats = PermissionService.get_user_usage_stats(user)

                security_logger.warning(
                    "Quota exceeded",
                    extra={
                        "event_type": "quota_exceeded",
                        "user_id": user.id,
                        "username": user.username,
                        "quota_used": usage_stats["used_today"],
                        "quota_limit": usage_stats["quota_daily"],
                        "requested_cost": cost,
                    }
                )

                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "message": f"Daily quota exceeded. You have used {usage_stats['used_today']} of {usage_stats['quota_daily']} actions. Quota resets at midnight UTC.",
                        "quota_used": usage_stats["used_today"],
                        "quota_limit": usage_stats["quota_daily"],
                        "quota_reset_date": usage_stats["reset_date"],
                    }
                )

            # Call the actual endpoint
            return await func(*args, **kwargs)

        return wrapper
    return decorator


def require_role(required_role: str):
    """
    Decorator to require specific user role for endpoint access

    Args:
        required_role: Required role ("user", "admin")

    Raises:
        HTTPException: 403 if user doesn't have required role

    Example:
        @router.get("/admin/users")
        @require_role("admin")
        async def list_users(user: User = Depends(get_current_user)):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs
            user = kwargs.get('user') or kwargs.get('current_user')

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            # Check role
            if not PermissionService.check_role_permission(user, required_role):
                security_logger.warning(
                    "Forbidden access attempt",
                    extra={
                        "event_type": "forbidden_access",
                        "user_id": user.id,
                        "username": user.username,
                        "current_role": user.role,
                        "required_role": required_role,
                    }
                )

                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "message": f"Access forbidden. Required role: {required_role}",
                        "current_role": user.role
                    }
                )

            # Call the actual endpoint
            return await func(*args, **kwargs)

        return wrapper
    return decorator


def track_usage(action_type: str):
    """
    Decorator to track action usage in audit log

    Args:
        action_type: Type of action being performed

    Example:
        @router.post("/actions/summarize")
        @track_usage("improve/summarize")
        async def summarize(user: User = Depends(get_current_user)):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs
            user = kwargs.get('user') or kwargs.get('current_user')

            if user:
                security_logger.info(
                    f"Action performed: {action_type}",
                    extra={
                        "event_type": "action_performed",
                        "user_id": user.id,
                        "username": user.username,
                        "action_type": action_type,
                    }
                )

            # Call the actual endpoint
            result = await func(*args, **kwargs)

            if user:
                security_logger.info(
                    f"Action completed: {action_type}",
                    extra={
                        "event_type": "action_completed",
                        "user_id": user.id,
                        "username": user.username,
                        "action_type": action_type,
                    }
                )

            return result

        return wrapper
    return decorator
