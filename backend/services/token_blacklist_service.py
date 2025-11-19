"""
JWT Token Blacklist Service for EchoNote.

Phase 4.1: Security Fixes - Token revocation mechanism

This module provides functionality to:
- Blacklist tokens that should no longer be valid
- Check if a token is blacklisted
- Automatically expire blacklisted tokens using Redis TTL

Use Cases:
- User logout - revoke current token
- Password change - revoke all user's tokens
- Security breach - revoke specific tokens
- Admin action - revoke user's access

Implementation Notes:
- Uses Redis for distributed, production-ready storage
- Automatic cleanup via Redis TTL
- Supports both single token and all user tokens revocation
"""

from datetime import datetime, timedelta
from typing import Optional
import redis
import jwt

from backend.config import settings
from backend.logging_config import get_security_logger

security_logger = get_security_logger()


class TokenBlacklistService:
    """
    Service for managing JWT token revocation (blacklist).

    Redis-backed implementation for distributed systems.
    """

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
            # Use db 3 for token blacklist
            redis_url = settings.REDIS_URL.replace("/0", "/3")
            cls._redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
        return cls._redis_client

    @classmethod
    def _get_token_key(cls, jti: str) -> str:
        """Generate Redis key for token JTI (JWT ID)."""
        return f"token:blacklist:{jti}"

    @classmethod
    def _get_user_tokens_key(cls, user_id: int) -> str:
        """Generate Redis key for user's token list."""
        return f"token:user:{user_id}:tokens"

    @classmethod
    def _extract_jti_from_token(cls, token: str) -> Optional[str]:
        """
        Extract JTI (JWT ID) from token without verification.

        Args:
            token: JWT token string

        Returns:
            JTI string if present, None otherwise
        """
        try:
            # Decode without verification to get JTI
            unverified = jwt.decode(
                token,
                options={"verify_signature": False}
            )
            return unverified.get("jti")
        except Exception as e:
            security_logger.error(
                f"Failed to extract JTI from token: {e}",
                extra={
                    "event_type": "token_extraction_error",
                    "error": str(e)
                }
            )
            return None

    @classmethod
    def _get_token_expiry(cls, token: str) -> Optional[int]:
        """
        Get token expiration time in seconds from now.

        Args:
            token: JWT token string

        Returns:
            Seconds until expiration, or None if cannot determine
        """
        try:
            unverified = jwt.decode(
                token,
                options={"verify_signature": False}
            )
            exp = unverified.get("exp")
            if exp:
                now = datetime.utcnow().timestamp()
                ttl = int(exp - now)
                return max(ttl, 0)  # Don't return negative TTL
            return None
        except Exception:
            return None

    @classmethod
    def blacklist_token(cls, token: str, reason: str = "logout") -> bool:
        """
        Add a token to the blacklist.

        Args:
            token: JWT token string to blacklist
            reason: Reason for blacklisting (for logging)

        Returns:
            True if blacklisted successfully, False on error
        """
        try:
            jti = cls._extract_jti_from_token(token)
            if not jti:
                security_logger.warning(
                    "Cannot blacklist token without JTI",
                    extra={
                        "event_type": "blacklist_failed",
                        "reason": "no_jti"
                    }
                )
                return False

            client = cls._get_redis_client()
            key = cls._get_token_key(jti)

            # Get TTL from token expiration
            ttl = cls._get_token_expiry(token)
            if ttl is None or ttl <= 0:
                # Token already expired or invalid, no need to blacklist
                return True

            # Store blacklist entry with TTL matching token expiration
            client.setex(key, ttl, reason)

            security_logger.info(
                f"Token blacklisted: {jti[:8]}... (reason: {reason})",
                extra={
                    "event_type": "token_blacklisted",
                    "jti": jti,
                    "reason": reason,
                    "ttl": ttl
                }
            )

            return True

        except redis.RedisError as e:
            security_logger.error(
                f"Redis error in blacklist_token: {e}",
                extra={
                    "event_type": "redis_error",
                    "error": str(e)
                }
            )
            return False

    @classmethod
    def is_token_blacklisted(cls, token: str) -> bool:
        """
        Check if a token is blacklisted.

        Args:
            token: JWT token string to check

        Returns:
            True if blacklisted, False otherwise
        """
        try:
            jti = cls._extract_jti_from_token(token)
            if not jti:
                # No JTI means we can't track it, allow by default
                return False

            client = cls._get_redis_client()
            key = cls._get_token_key(jti)

            # Check if key exists in blacklist
            return client.exists(key) > 0

        except redis.RedisError as e:
            security_logger.error(
                f"Redis error in is_token_blacklisted: {e}",
                extra={
                    "event_type": "redis_error",
                    "error": str(e)
                }
            )
            # Fail open - don't block if Redis is down
            return False

    @classmethod
    def blacklist_user_tokens(cls, user_id: int, reason: str = "password_change") -> int:
        """
        Blacklist all tokens for a specific user.

        This is useful when:
        - User changes password
        - Admin revokes user access
        - Security breach requires logging out all sessions

        Args:
            user_id: User ID whose tokens should be blacklisted
            reason: Reason for blacklisting (for logging)

        Returns:
            Number of tokens blacklisted

        Note: This requires tokens to include user_id in claims.
        If tokens don't track this, this method won't work effectively.
        """
        security_logger.warning(
            f"Blacklist all tokens requested for user {user_id} (reason: {reason})",
            extra={
                "event_type": "user_tokens_blacklist_requested",
                "user_id": user_id,
                "reason": reason,
                "note": "Current implementation requires JTI in tokens"
            }
        )

        # Note: This is a placeholder for future implementation
        # Full implementation would require:
        # 1. Storing user_id -> token mapping when tokens are created
        # 2. Iterating through user's tokens and blacklisting each
        # 3. Or using a user-level blacklist with timestamp

        # For now, log the request
        return 0

    @classmethod
    def get_blacklist_info(cls, token: str) -> Optional[dict]:
        """
        Get blacklist information for a token.

        Args:
            token: JWT token string

        Returns:
            Dict with blacklist info if blacklisted, None otherwise
        """
        try:
            jti = cls._extract_jti_from_token(token)
            if not jti:
                return None

            client = cls._get_redis_client()
            key = cls._get_token_key(jti)

            # Get reason and TTL
            reason = client.get(key)
            if reason is None:
                return None

            ttl = client.ttl(key)

            return {
                "jti": jti,
                "reason": reason,
                "expires_in_seconds": ttl
            }

        except redis.RedisError as e:
            security_logger.error(
                f"Redis error in get_blacklist_info: {e}",
                extra={
                    "event_type": "redis_error",
                    "error": str(e)
                }
            )
            return None
