"""
Admin API Router - Administrative endpoints for user and system management.

This router provides admin-only endpoints for:
- User management (list, view details, modify quotas/roles/status)
- AI actions monitoring across all users
- System-wide statistics
- Security audit log viewing

All endpoints require admin role authentication.
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select, func, and_, or_
from pydantic import BaseModel

from backend.auth import get_current_active_user
from backend.database import get_session
from backend.models import User, AIAction, Transcription
from backend.services.permission_service import PermissionService
from backend.logging_config import get_logger, get_security_logger

logger = get_logger(__name__)
security_logger = get_security_logger()

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"],
    dependencies=[Depends(get_current_active_user)]
)


# ============================================================================
# Dependency: Require Admin Role
# ============================================================================

async def require_admin_role(current_user: User = Depends(get_current_active_user)) -> User:
    """Dependency to ensure user has admin role."""
    if current_user.role != "admin":
        security_logger.warning(
            f"Non-admin user attempted admin endpoint access",
            extra={
                "user_id": current_user.id,
                "username": current_user.username,
                "role": current_user.role
            }
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access forbidden. Required role: admin. Current role: {current_user.role}"
        )
    return current_user


# ============================================================================
# Schemas
# ============================================================================

class UserListItem(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_premium: bool
    is_active: bool
    ai_action_quota_daily: int
    ai_action_count_today: int
    created_at: datetime
    transcription_count: int
    ai_action_count: int


class UserList(BaseModel):
    users: list[UserListItem]
    total: int
    skip: int
    limit: int


class UserDetailStatistics(BaseModel):
    transcriptions: dict
    ai_actions: dict


class UserDetailResponse(BaseModel):
    user: dict
    statistics: UserDetailStatistics


class AIActionListItem(BaseModel):
    id: int
    action_id: str
    user_id: int
    username: str
    transcription_id: int
    action_type: str
    status: str
    quota_cost: int
    created_at: datetime
    completed_at: Optional[datetime]
    processing_duration_ms: Optional[int]


class AIActionList(BaseModel):
    actions: list[AIActionListItem]
    total: int
    skip: int
    limit: int


class SystemStats(BaseModel):
    users: dict
    transcriptions: dict
    ai_actions: dict
    quotas: dict


class QuotaUpdate(BaseModel):
    ai_action_quota_daily: int


class RoleUpdate(BaseModel):
    role: str


class PremiumUpdate(BaseModel):
    is_premium: bool


class ActiveUpdate(BaseModel):
    is_active: bool


# ============================================================================
# User Management Endpoints
# ============================================================================

@router.get("/users", response_model=UserList, status_code=status.HTTP_200_OK)
async def list_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    role: Optional[str] = Query(default=None),
    is_premium: Optional[bool] = Query(default=None),
    search: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin_role)
):
    """
    List all users with pagination and filters.

    **Admin Only**

    **Query Parameters:**
    - `skip`: Number of records to skip (default: 0)
    - `limit`: Maximum records to return (default: 20, max: 100)
    - `role`: Filter by role (user, admin)
    - `is_premium`: Filter by premium status
    - `search`: Search username or email

    **Returns:**
    - List of users with counts of transcriptions and AI actions
    """
    # Build query
    query = select(User)

    # Apply filters
    if role:
        query = query.where(User.role == role)
    if is_premium is not None:
        query = query.where(User.is_premium == is_premium)
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                User.username.like(search_pattern),
                User.email.like(search_pattern)
            )
        )

    # Get total count
    count_query = select(func.count()).select_from(User)
    if role:
        count_query = count_query.where(User.role == role)
    if is_premium is not None:
        count_query = count_query.where(User.is_premium == is_premium)
    if search:
        search_pattern = f"%{search}%"
        count_query = count_query.where(
            or_(
                User.username.like(search_pattern),
                User.email.like(search_pattern)
            )
        )

    total = session.exec(count_query).one()

    # Apply pagination
    query = query.offset(skip).limit(limit)

    # Execute query
    users = session.exec(query).all()

    # Build response with counts
    user_items = []
    for user in users:
        # Count transcriptions
        transcription_count = session.exec(
            select(func.count()).select_from(Transcription).where(Transcription.user_id == user.id)
        ).one()

        # Count AI actions
        ai_action_count = session.exec(
            select(func.count()).select_from(AIAction).where(AIAction.user_id == user.id)
        ).one()

        user_items.append(UserListItem(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            is_premium=user.is_premium,
            is_active=user.is_active,
            ai_action_quota_daily=user.ai_action_quota_daily,
            ai_action_count_today=user.ai_action_count_today,
            created_at=user.created_at,
            transcription_count=transcription_count,
            ai_action_count=ai_action_count
        ))

    logger.info(
        f"Admin user list accessed",
        extra={
            "admin_user_id": current_user.id,
            "admin_username": current_user.username,
            "total_users": total,
            "skip": skip,
            "limit": limit
        }
    )

    return UserList(
        users=user_items,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/users/{user_id}", response_model=UserDetailResponse, status_code=status.HTTP_200_OK)
async def get_user_details(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin_role)
):
    """
    Get detailed user information and statistics.

    **Admin Only**

    **Returns:**
    - User details
    - Transcription statistics
    - AI action statistics broken down by type
    """
    # Get user
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}"
        )

    # Get transcription counts
    total_transcriptions = session.exec(
        select(func.count()).select_from(Transcription).where(Transcription.user_id == user_id)
    ).one()

    # Get transcriptions this month
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    transcriptions_this_month = session.exec(
        select(func.count()).select_from(Transcription)
        .where(and_(Transcription.user_id == user_id, Transcription.created_at >= month_start))
    ).one()

    # Get AI action counts
    total_ai_actions = session.exec(
        select(func.count()).select_from(AIAction).where(AIAction.user_id == user_id)
    ).one()

    ai_actions_this_month = session.exec(
        select(func.count()).select_from(AIAction)
        .where(and_(AIAction.user_id == user_id, AIAction.created_at >= month_start))
    ).one()

    ai_actions_today = user.ai_action_count_today

    # Get AI actions by type
    actions_by_type_query = select(AIAction.action_type, func.count(AIAction.id)).where(
        AIAction.user_id == user_id
    ).group_by(AIAction.action_type)

    actions_by_type_results = session.exec(actions_by_type_query).all()
    actions_by_type = {action_type: count for action_type, count in actions_by_type_results}

    # Build response
    user_dict = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_premium": user.is_premium,
        "is_active": user.is_active,
        "ai_action_quota_daily": user.ai_action_quota_daily,
        "ai_action_count_today": user.ai_action_count_today,
        "quota_reset_date": str(user.quota_reset_date),
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat() if user.updated_at else None
    }

    statistics = UserDetailStatistics(
        transcriptions={
            "total": total_transcriptions,
            "this_month": transcriptions_this_month
        },
        ai_actions={
            "total": total_ai_actions,
            "this_month": ai_actions_this_month,
            "today": ai_actions_today,
            "by_type": actions_by_type
        }
    )

    logger.info(
        f"Admin viewed user details",
        extra={
            "admin_user_id": current_user.id,
            "admin_username": current_user.username,
            "viewed_user_id": user_id
        }
    )

    return UserDetailResponse(
        user=user_dict,
        statistics=statistics
    )


@router.patch("/users/{user_id}/quota", status_code=status.HTTP_200_OK)
async def update_user_quota(
    user_id: int,
    quota_update: QuotaUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin_role)
):
    """
    Adjust user's daily quota.

    **Admin Only**

    **Request Body:**
    - `ai_action_quota_daily`: New daily quota limit

    **Returns:**
    - Updated user object
    """
    # Get user
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}"
        )

    old_quota = user.ai_action_quota_daily
    user.ai_action_quota_daily = quota_update.ai_action_quota_daily
    user.updated_at = datetime.utcnow()

    session.add(user)
    session.commit()
    session.refresh(user)

    security_logger.info(
        f"Admin updated user quota",
        extra={
            "admin_user_id": current_user.id,
            "admin_username": current_user.username,
            "user_id": user_id,
            "username": user.username,
            "old_quota": old_quota,
            "new_quota": quota_update.ai_action_quota_daily
        }
    )

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_premium": user.is_premium,
        "ai_action_quota_daily": user.ai_action_quota_daily,
        "ai_action_count_today": user.ai_action_count_today
    }


@router.patch("/users/{user_id}/role", status_code=status.HTTP_200_OK)
async def update_user_role(
    user_id: int,
    role_update: RoleUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin_role)
):
    """
    Change user's role.

    **Admin Only**

    **Request Body:**
    - `role`: New role (user or admin)

    **Returns:**
    - Updated user object
    """
    # Validate role
    if role_update.role not in ["user", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {role_update.role}. Must be 'user' or 'admin'"
        )

    # Get user
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}"
        )

    old_role = user.role
    user.role = role_update.role
    user.updated_at = datetime.utcnow()

    session.add(user)
    session.commit()
    session.refresh(user)

    security_logger.warning(
        f"Admin changed user role",
        extra={
            "admin_user_id": current_user.id,
            "admin_username": current_user.username,
            "user_id": user_id,
            "username": user.username,
            "old_role": old_role,
            "new_role": role_update.role
        }
    )

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_premium": user.is_premium,
        "ai_action_quota_daily": user.ai_action_quota_daily
    }


@router.patch("/users/{user_id}/premium", status_code=status.HTTP_200_OK)
async def update_user_premium(
    user_id: int,
    premium_update: PremiumUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin_role)
):
    """
    Toggle user's premium status.

    **Admin Only**

    **Request Body:**
    - `is_premium`: New premium status (true or false)

    **Returns:**
    - Updated user object
    """
    # Get user
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}"
        )

    old_premium = user.is_premium
    user.is_premium = premium_update.is_premium
    user.updated_at = datetime.utcnow()

    # If upgrading to premium, increase quota
    if premium_update.is_premium and not old_premium:
        user.ai_action_quota_daily = 1000  # Premium quota

    # If downgrading from premium, reset to default
    if not premium_update.is_premium and old_premium:
        user.ai_action_quota_daily = 100  # Default quota

    session.add(user)
    session.commit()
    session.refresh(user)

    security_logger.info(
        f"Admin changed user premium status",
        extra={
            "admin_user_id": current_user.id,
            "admin_username": current_user.username,
            "user_id": user_id,
            "username": user.username,
            "old_premium": old_premium,
            "new_premium": premium_update.is_premium,
            "new_quota": user.ai_action_quota_daily
        }
    )

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_premium": user.is_premium,
        "ai_action_quota_daily": user.ai_action_quota_daily
    }


@router.patch("/users/{user_id}/active", status_code=status.HTTP_200_OK)
async def update_user_active(
    user_id: int,
    active_update: ActiveUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin_role)
):
    """
    Activate/deactivate user account.

    **Admin Only**

    **Request Body:**
    - `is_active`: New active status (true or false)

    **Returns:**
    - Updated user object
    """
    # Get user
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}"
        )

    old_active = user.is_active
    user.is_active = active_update.is_active
    user.updated_at = datetime.utcnow()

    session.add(user)
    session.commit()
    session.refresh(user)

    security_logger.warning(
        f"Admin changed user active status",
        extra={
            "admin_user_id": current_user.id,
            "admin_username": current_user.username,
            "user_id": user_id,
            "username": user.username,
            "old_active": old_active,
            "new_active": active_update.is_active
        }
    )

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active
    }


# ============================================================================
# AI Actions Monitoring
# ============================================================================

@router.get("/actions", response_model=AIActionList, status_code=status.HTTP_200_OK)
async def list_all_actions(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    user_id: Optional[int] = Query(default=None),
    action_type: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin_role)
):
    """
    List all AI actions across all users.

    **Admin Only**

    **Query Parameters:**
    - `skip`: Number of records to skip (default: 0)
    - `limit`: Maximum records to return (default: 50, max: 100)
    - `user_id`: Filter by user ID
    - `action_type`: Filter by action type
    - `status`: Filter by status
    - `date_from`: Filter by start date (ISO format)
    - `date_to`: Filter by end date (ISO format)

    **Returns:**
    - List of AI actions with user information
    """
    # Build query with user join
    query = select(AIAction, User).join(User, AIAction.user_id == User.id)

    # Apply filters
    filters = []
    if user_id:
        filters.append(AIAction.user_id == user_id)
    if action_type:
        filters.append(AIAction.action_type == action_type)
    if status_filter:
        filters.append(AIAction.status == status_filter)
    if date_from:
        try:
            date_from_dt = datetime.fromisoformat(date_from)
            filters.append(AIAction.created_at >= date_from_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid date format for date_from: {date_from}. Use ISO format."
            )
    if date_to:
        try:
            date_to_dt = datetime.fromisoformat(date_to)
            filters.append(AIAction.created_at <= date_to_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid date format for date_to: {date_to}. Use ISO format."
            )

    if filters:
        query = query.where(and_(*filters))

    # Get total count
    count_query = select(func.count()).select_from(AIAction)
    if filters:
        count_query = count_query.where(and_(*filters))
    total = session.exec(count_query).one()

    # Apply pagination and ordering
    query = query.order_by(AIAction.created_at.desc()).offset(skip).limit(limit)

    # Execute query
    results = session.exec(query).all()

    # Build response
    action_items = []
    for action, user in results:
        action_items.append(AIActionListItem(
            id=action.id,
            action_id=action.action_id,
            user_id=action.user_id,
            username=user.username,
            transcription_id=action.transcription_id,
            action_type=action.action_type,
            status=action.status,
            quota_cost=action.quota_cost,
            created_at=action.created_at,
            completed_at=action.completed_at,
            processing_duration_ms=action.processing_duration_ms
        ))

    logger.info(
        f"Admin accessed AI actions list",
        extra={
            "admin_user_id": current_user.id,
            "admin_username": current_user.username,
            "total_actions": total,
            "filters": {
                "user_id": user_id,
                "action_type": action_type,
                "status": status_filter,
                "date_from": date_from,
                "date_to": date_to
            }
        }
    )

    return AIActionList(
        actions=action_items,
        total=total,
        skip=skip,
        limit=limit
    )


# ============================================================================
# System Statistics
# ============================================================================

@router.get("/stats", response_model=SystemStats, status_code=status.HTTP_200_OK)
async def get_system_stats(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin_role)
):
    """
    Get system-wide statistics dashboard.

    **Admin Only**

    **Returns:**
    - User statistics
    - Transcription statistics
    - AI action statistics (by type, by status)
    - Quota statistics
    """
    # User statistics
    total_users = session.exec(select(func.count()).select_from(User)).one()
    active_users = session.exec(select(func.count()).select_from(User).where(User.is_active == True)).one()
    premium_users = session.exec(select(func.count()).select_from(User).where(User.is_premium == True)).one()
    admins = session.exec(select(func.count()).select_from(User).where(User.role == "admin")).one()

    # New users this month
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_users_this_month = session.exec(
        select(func.count()).select_from(User).where(User.created_at >= month_start)
    ).one()

    # Transcription statistics
    total_transcriptions = session.exec(select(func.count()).select_from(Transcription)).one()
    transcriptions_this_month = session.exec(
        select(func.count()).select_from(Transcription).where(Transcription.created_at >= month_start)
    ).one()
    transcriptions_today = session.exec(
        select(func.count()).select_from(Transcription)
        .where(Transcription.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0))
    ).one()

    # AI action statistics
    total_ai_actions = session.exec(select(func.count()).select_from(AIAction)).one()
    ai_actions_this_month = session.exec(
        select(func.count()).select_from(AIAction).where(AIAction.created_at >= month_start)
    ).one()
    ai_actions_today = session.exec(
        select(func.count()).select_from(AIAction)
        .where(AIAction.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0))
    ).one()

    # AI actions by type (aggregate by category)
    actions_by_type_query = select(AIAction.action_type, func.count(AIAction.id)).group_by(AIAction.action_type)
    actions_by_type_results = session.exec(actions_by_type_query).all()

    # Aggregate into categories
    by_type = {
        "analyze": 0,
        "create/*": 0,
        "improve/*": 0,
        "translate/*": 0,
        "voice/*": 0
    }

    for action_type, count in actions_by_type_results:
        if action_type == "analyze":
            by_type["analyze"] += count
        elif action_type.startswith("create/"):
            by_type["create/*"] += count
        elif action_type.startswith("improve/"):
            by_type["improve/*"] += count
        elif action_type.startswith("translate/"):
            by_type["translate/*"] += count
        elif action_type.startswith("voice/"):
            by_type["voice/*"] += count

    # AI actions by status
    actions_by_status_query = select(AIAction.status, func.count(AIAction.id)).group_by(AIAction.status)
    actions_by_status_results = session.exec(actions_by_status_query).all()
    by_status = {status_val: count for status_val, count in actions_by_status_results}

    # Quota statistics
    total_allocated_query = select(func.sum(User.ai_action_quota_daily)).select_from(User)
    total_allocated = session.exec(total_allocated_query).one() or 0

    used_today_query = select(func.sum(User.ai_action_count_today)).select_from(User)
    used_today = session.exec(used_today_query).one() or 0

    average_per_user = int(used_today / total_users) if total_users > 0 else 0

    logger.info(
        f"Admin accessed system statistics",
        extra={
            "admin_user_id": current_user.id,
            "admin_username": current_user.username
        }
    )

    return SystemStats(
        users={
            "total": total_users,
            "active": active_users,
            "premium": premium_users,
            "admins": admins,
            "new_this_month": new_users_this_month
        },
        transcriptions={
            "total": total_transcriptions,
            "this_month": transcriptions_this_month,
            "today": transcriptions_today
        },
        ai_actions={
            "total": total_ai_actions,
            "this_month": ai_actions_this_month,
            "today": ai_actions_today,
            "by_type": by_type,
            "by_status": by_status
        },
        quotas={
            "total_allocated": total_allocated,
            "used_today": used_today,
            "average_per_user": average_per_user
        }
    )
