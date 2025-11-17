"""
Permission Service

Handles user quota management, role-based permissions, and usage tracking.
"""

from datetime import datetime, date
from typing import Dict
from sqlmodel import Session, select
from backend.models import User
from backend.logging_config import get_logger, get_security_logger

logger = get_logger(__name__)
security_logger = get_security_logger()


# Quota costs for different action types
QUOTA_COSTS = {
    "analyze": 1,
    # Create actions cost more (content generation)
    "create/linkedin-post": 2,
    "create/email-draft": 2,
    "create/blog-post": 2,
    "create/social-media-caption": 2,
    # Improve/transform actions
    "improve/summarize": 1,
    "improve/summarize-bullets": 1,
    "improve/rewrite-formal": 1,
    "improve/rewrite-friendly": 1,
    "improve/rewrite-simple": 1,
    "improve/expand": 1,
    "improve/shorten": 1,
    # Translation actions
    "translate/to-english": 1,
    "translate/to-swedish": 1,
    "translate/to-czech": 1,
    # Voice-specific actions
    "voice/clean-filler-words": 1,
    "voice/fix-grammar": 1,
    "voice/convert-spoken-to-written": 1,
}


class PermissionService:
    """Service for managing user permissions and quotas"""

    @staticmethod
    def check_user_quota(user: User, quota_cost: int = 1) -> bool:
        """
        Check if user has sufficient quota for the action

        Args:
            user: User instance
            quota_cost: Number of quota units required

        Returns:
            True if user has sufficient quota, False otherwise
        """
        # Admins bypass quota checks
        if user.role == "admin":
            return True

        # Auto-reset quota if date has changed
        today = datetime.utcnow().date()
        if user.quota_reset_date < today:
            # Quota needs reset but we'll return current state
            # Actual reset will happen in increment_usage or via scheduled task
            return quota_cost <= user.ai_action_quota_daily

        # Check if user has sufficient remaining quota
        remaining = user.ai_action_quota_daily - user.ai_action_count_today
        return remaining >= quota_cost

    @staticmethod
    def increment_usage(
        session: Session,
        user: User,
        action_type: str,
        quota_cost: int = 1
    ) -> None:
        """
        Increment user's quota usage

        Args:
            session: Database session
            user: User instance
            action_type: Type of action being performed
            quota_cost: Number of quota units to consume
        """
        # Admins don't consume quota
        if user.role == "admin":
            logger.info(
                f"Admin user {user.username} performed action {action_type} (quota not consumed)"
            )
            return

        # Auto-reset if needed
        today = datetime.utcnow().date()
        if user.quota_reset_date < today:
            user.ai_action_count_today = 0
            user.quota_reset_date = today
            logger.info(f"Auto-reset quota for user {user.username}")

        # Increment usage
        user.ai_action_count_today += quota_cost
        user.updated_at = datetime.utcnow()

        session.add(user)
        session.commit()

        logger.info(
            f"User {user.username} consumed {quota_cost} quota for {action_type}. "
            f"Usage: {user.ai_action_count_today}/{user.ai_action_quota_daily}"
        )

        # Log to security log for audit trail
        security_logger.info(
            "Quota consumed",
            extra={
                "event_type": "quota_consumed",
                "user_id": user.id,
                "username": user.username,
                "action_type": action_type,
                "quota_cost": quota_cost,
                "quota_used": user.ai_action_count_today,
                "quota_limit": user.ai_action_quota_daily,
            }
        )

    @staticmethod
    def reset_daily_quotas(session: Session) -> int:
        """
        Reset daily quotas for all users

        Called by scheduled task at midnight UTC

        Args:
            session: Database session

        Returns:
            Number of users whose quotas were reset
        """
        today = datetime.utcnow().date()

        # Find all users whose quota needs reset
        statement = select(User).where(User.quota_reset_date < today)
        users = session.exec(statement).all()

        count = 0
        for user in users:
            user.ai_action_count_today = 0
            user.quota_reset_date = today
            user.updated_at = datetime.utcnow()
            session.add(user)
            count += 1

        session.commit()

        logger.info(f"Reset daily quotas for {count} users")
        security_logger.info(
            "Daily quota reset completed",
            extra={
                "event_type": "quota_reset",
                "users_reset": count,
                "reset_date": today.isoformat()
            }
        )

        return count

    @staticmethod
    def get_user_usage_stats(user: User) -> Dict:
        """
        Get current user usage statistics

        Args:
            user: User instance

        Returns:
            Dictionary with usage statistics
        """
        # Auto-adjust for date change
        today = datetime.utcnow().date()
        used_today = user.ai_action_count_today
        if user.quota_reset_date < today:
            used_today = 0  # Will be reset on next action

        remaining = user.ai_action_quota_daily - used_today

        return {
            "quota_daily": user.ai_action_quota_daily,
            "used_today": used_today,
            "remaining_today": max(0, remaining),
            "reset_date": (today if user.quota_reset_date < today else user.quota_reset_date + __import__('datetime').timedelta(days=1)).isoformat(),
            "is_premium": user.is_premium,
            "role": user.role,
        }

    @staticmethod
    def check_role_permission(user: User, required_role: str) -> bool:
        """
        Check if user has required role

        Role hierarchy: admin > user

        Args:
            user: User instance
            required_role: Required role (e.g., "admin")

        Returns:
            True if user has required role or higher
        """
        if required_role == "admin":
            return user.role == "admin"

        # Everyone has "user" level access if active
        if required_role == "user":
            return user.is_active

        return False

    @staticmethod
    def get_quota_cost(action_type: str) -> int:
        """
        Get quota cost for specific action type

        Args:
            action_type: Type of action (e.g., "analyze", "create/linkedin-post")

        Returns:
            Quota cost (defaults to 1 if not found)
        """
        return QUOTA_COSTS.get(action_type, 1)
