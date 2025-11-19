"""
Authentication security service for EchoNote.

Phase 4: Security Hardening - Failed login tracking and account lockout
Phase 4.1: Security Fixes - Redis-backed storage for distributed systems

This module provides functionality to:
- Track failed login attempts per username
- Automatically lock accounts after too many failed attempts
- Clear attempts on successful login
- Provide lockout information to users

Implementation Notes:
- Uses Redis for distributed, production-ready storage
- Supports multiple application instances (workers, containers)
- Lockout is temporary (15 minutes by default)
- Thread-safe with Redis atomic operations
- Automatic expiration of old data via Redis TTL
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
import json
import redis

from backend.config import settings
from backend.logging_config import get_security_logger

security_logger = get_security_logger()


class AuthSecurityService:
    """
    Service for tracking failed login attempts and account lockout.

    Redis-backed implementation for distributed systems.
    All methods use Redis for storage, ensuring consistency across
    multiple application instances.
    """

    # Configuration
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15
    ATTEMPT_WINDOW_MINUTES = 60  # Reset counter if no attempts in this time

    # Redis client (shared, lazy-initialized)
    _redis_client: Optional[redis.Redis] = None

    @classmethod
    def _get_redis_client(cls) -> redis.Redis:
        """
        Get or create Redis client.

        Returns:
            Redis client instance
        """
        if cls._redis_client is None:
            # Use same Redis as rate limiter (db 2)
            redis_url = settings.REDIS_URL.replace("/0", "/2")  # Use db 2 for auth tracking
            cls._redis_client = redis.from_url(
                redis_url,
                decode_responses=True,  # Auto-decode strings
                socket_connect_timeout=5,
                socket_timeout=5
            )
        return cls._redis_client

    @classmethod
    def _get_key(cls, username: str) -> str:
        """Generate Redis key for username."""
        return f"auth:failed_attempts:{username}"

    @classmethod
    def _get_lock_key(cls, username: str) -> str:
        """Generate Redis key for account lockout."""
        return f"auth:locked:{username}"

    @classmethod
    def record_failed_login(cls, username: str) -> Tuple[int, Optional[datetime]]:
        """
        Record a failed login attempt.

        Args:
            username: The username that failed to login

        Returns:
            Tuple of (attempts_remaining, locked_until)
            - attempts_remaining: Number of attempts before lockout (0 if locked)
            - locked_until: datetime when account will be unlocked (None if not locked)
        """
        try:
            client = cls._get_redis_client()
            key = cls._get_key(username)
            lock_key = cls._get_lock_key(username)
            now = datetime.utcnow()

            # Increment failed attempts (atomic operation)
            attempts = client.incr(key)

            # Set expiration on first attempt
            if attempts == 1:
                client.expire(key, cls.ATTEMPT_WINDOW_MINUTES * 60)

                security_logger.warning(
                    f"Failed login attempt for '{username}' (1/{cls.MAX_FAILED_ATTEMPTS})",
                    extra={
                        "event_type": "failed_login",
                        "username": username,
                        "attempts": 1,
                        "attempts_remaining": cls.MAX_FAILED_ATTEMPTS - 1
                    }
                )

                return cls.MAX_FAILED_ATTEMPTS - 1, None

            # Check if should lock account
            if attempts >= cls.MAX_FAILED_ATTEMPTS:
                locked_until = now + timedelta(minutes=cls.LOCKOUT_DURATION_MINUTES)

                # Store lockout timestamp
                client.setex(
                    lock_key,
                    cls.LOCKOUT_DURATION_MINUTES * 60,
                    locked_until.isoformat()
                )

                security_logger.error(
                    f"Account locked for '{username}' after {cls.MAX_FAILED_ATTEMPTS} failed attempts",
                    extra={
                        "event_type": "account_locked",
                        "username": username,
                        "failed_attempts": attempts,
                        "locked_until": locked_until.isoformat()
                    }
                )

                return 0, locked_until

            # Not locked yet
            attempts_remaining = cls.MAX_FAILED_ATTEMPTS - attempts

            security_logger.warning(
                f"Failed login attempt for '{username}' ({attempts}/{cls.MAX_FAILED_ATTEMPTS})",
                extra={
                    "event_type": "failed_login",
                    "username": username,
                    "attempts": attempts,
                    "attempts_remaining": attempts_remaining
                }
            )

            return attempts_remaining, None

        except redis.RedisError as e:
            security_logger.error(
                f"Redis error in record_failed_login: {e}",
                extra={
                    "event_type": "redis_error",
                    "username": username,
                    "error": str(e)
                }
            )
            # Fail open - don't block login if Redis is down
            return cls.MAX_FAILED_ATTEMPTS - 1, None

    @classmethod
    def is_locked(cls, username: str) -> Tuple[bool, Optional[datetime]]:
        """
        Check if an account is currently locked.

        Args:
            username: The username to check

        Returns:
            Tuple of (is_locked, locked_until)
            - is_locked: True if account is locked
            - locked_until: datetime when account will be unlocked (None if not locked)
        """
        try:
            client = cls._get_redis_client()
            lock_key = cls._get_lock_key(username)

            # Check if lockout key exists
            locked_until_str = client.get(lock_key)

            if locked_until_str is None:
                return False, None

            # Parse lockout timestamp
            locked_until = datetime.fromisoformat(locked_until_str)
            now = datetime.utcnow()

            # Check if lockout has expired (Redis TTL handles this, but double-check)
            if now >= locked_until:
                # Redis TTL should have removed it, but clean up just in case
                client.delete(lock_key)
                client.delete(cls._get_key(username))

                security_logger.info(
                    f"Account '{username}' automatically unlocked after timeout",
                    extra={
                        "event_type": "account_unlocked",
                        "username": username,
                        "unlock_reason": "timeout_expired"
                    }
                )

                return False, None

            # Still locked
            return True, locked_until

        except redis.RedisError as e:
            security_logger.error(
                f"Redis error in is_locked: {e}",
                extra={
                    "event_type": "redis_error",
                    "username": username,
                    "error": str(e)
                }
            )
            # Fail open - don't block login if Redis is down
            return False, None

    @classmethod
    def clear_attempts(cls, username: str):
        """
        Clear failed login attempts for a user (called on successful login).

        Args:
            username: The username to clear attempts for
        """
        try:
            client = cls._get_redis_client()
            key = cls._get_key(username)
            lock_key = cls._get_lock_key(username)

            # Get current attempts before deleting
            attempts = client.get(key)

            if attempts:
                security_logger.info(
                    f"Cleared {attempts} failed login attempts for '{username}'",
                    extra={
                        "event_type": "login_attempts_cleared",
                        "username": username,
                        "cleared_attempts": int(attempts)
                    }
                )

            # Delete both keys (atomic with pipeline)
            pipe = client.pipeline()
            pipe.delete(key)
            pipe.delete(lock_key)
            pipe.execute()

        except redis.RedisError as e:
            security_logger.error(
                f"Redis error in clear_attempts: {e}",
                extra={
                    "event_type": "redis_error",
                    "username": username,
                    "error": str(e)
                }
            )
            # Continue - clearing attempts is not critical

    @classmethod
    def get_lockout_message(cls, locked_until: datetime) -> str:
        """
        Generate a user-friendly lockout message.

        Args:
            locked_until: When the account will be unlocked

        Returns:
            Human-readable message about the lockout
        """
        now = datetime.utcnow()
        time_remaining = locked_until - now

        minutes_remaining = int(time_remaining.total_seconds() / 60)
        if minutes_remaining < 1:
            return "Account temporarily locked. Please try again in a moment."
        else:
            return f"Account temporarily locked due to multiple failed login attempts. Please try again in {minutes_remaining} minute(s)."

    @classmethod
    def get_attempt_count(cls, username: str) -> int:
        """
        Get current failed attempt count for a username.

        Args:
            username: The username to check

        Returns:
            Number of failed attempts (0 if none)
        """
        try:
            client = cls._get_redis_client()
            key = cls._get_key(username)
            attempts = client.get(key)
            return int(attempts) if attempts else 0
        except redis.RedisError as e:
            security_logger.error(
                f"Redis error in get_attempt_count: {e}",
                extra={
                    "event_type": "redis_error",
                    "username": username,
                    "error": str(e)
                }
            )
            return 0

    @classmethod
    def cleanup_old_attempts(cls, older_than_hours: int = 24):
        """
        Clean up old login attempt records (maintenance task).

        Note: With Redis-backed storage using TTL, this is mostly automatic.
        This method is kept for API compatibility but does minimal work.

        Args:
            older_than_hours: Remove attempts older than this many hours (unused with Redis TTL)
        """
        # Redis TTL automatically handles cleanup
        # This method is kept for compatibility but is now a no-op
        security_logger.info(
            "Login attempts cleanup called (automatic with Redis TTL)",
            extra={
                "event_type": "login_attempts_cleanup",
                "note": "Redis TTL handles automatic expiration"
            }
        )
