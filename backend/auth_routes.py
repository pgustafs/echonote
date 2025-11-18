"""
Authentication routes for EchoNote.

Provides endpoints for user registration, login, and user management.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select, func, and_
from pydantic import BaseModel

from backend.auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_password_hash,
    get_user_by_email,
    get_user_by_username,
)
from backend.config import settings
from backend.database import get_session
from backend.models import Token, User, UserCreate, UserLogin, UserPublic, AIAction
from backend.logging_config import get_logger, get_security_logger

logger = get_logger(__name__)
security_logger = get_security_logger()

router = APIRouter(prefix="/api/auth", tags=["authentication"])


# ============================================================================
# Schemas for Usage Endpoints
# ============================================================================

class UsageQuota(BaseModel):
    daily_limit: int
    used_today: int
    remaining_today: int
    reset_date: str
    is_premium: bool


class UsageHistory(BaseModel):
    total_actions: int
    this_month: int
    this_week: int
    today: int


class UsageResponse(BaseModel):
    quota: UsageQuota
    usage_history: UsageHistory
    breakdown_by_type: dict


class UserActionListItem(BaseModel):
    action_id: str
    action_type: str
    status: str
    transcription_id: int
    quota_cost: int
    created_at: datetime
    completed_at: Optional[datetime]


class UserActionList(BaseModel):
    actions: list[UserActionListItem]
    total: int
    skip: int
    limit: int


class ActionDetailResponse(BaseModel):
    action_id: str
    action_type: str
    status: str
    message: str
    transcription_id: int
    quota_cost: int
    created_at: datetime
    completed_at: Optional[datetime]
    result: Optional[dict]
    error: Optional[str]


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, session: Session = Depends(get_session)):
    """
    Register a new user account.

    Args:
        user_data: User registration data (username, email, password)
        session: Database session

    Returns:
        UserPublic: The created user (without password)

    Raises:
        HTTPException: If username or email already exists
    """
    # Check if username already exists
    existing_user = get_user_by_username(session, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email already exists
    existing_email = get_user_by_email(session, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    logger.info(f"New user registered: {db_user.username}")
    security_logger.info(
        "User registered",
        extra={
            "event_type": "user_registered",
            "user_id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
        }
    )

    return UserPublic(
        id=db_user.id,
        username=db_user.username,
        email=db_user.email,
        created_at=db_user.created_at,
        is_active=db_user.is_active,
        role=db_user.role,
        is_premium=db_user.is_premium,
        ai_action_quota_daily=db_user.ai_action_quota_daily,
        ai_action_count_today=db_user.ai_action_count_today,
        quota_reset_date=db_user.quota_reset_date
    )


@router.post("/login", response_model=Token)
def login(user_data: UserLogin, session: Session = Depends(get_session)):
    """
    Login with username and password to get JWT token.

    Args:
        user_data: User login credentials (username, password)
        session: Database session

    Returns:
        Token: JWT access token

    Raises:
        HTTPException: If credentials are invalid
    """
    user = authenticate_user(session, user_data.username, user_data.password)
    if not user:
        security_logger.warning(
            "Failed login attempt",
            extra={
                "event_type": "login_failed",
                "username": user_data.username,
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    logger.info(f"User logged in: {user.username}")
    security_logger.info(
        "User logged in successfully",
        extra={
            "event_type": "login_success",
            "user_id": user.id,
            "username": user.username,
        }
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserPublic)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user information.

    Args:
        current_user: The authenticated user from JWT token

    Returns:
        UserPublic: Current user information
    """
    return UserPublic(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        created_at=current_user.created_at,
        is_active=current_user.is_active,
        role=current_user.role,
        is_premium=current_user.is_premium,
        ai_action_quota_daily=current_user.ai_action_quota_daily,
        ai_action_count_today=current_user.ai_action_count_today,
        quota_reset_date=current_user.quota_reset_date
    )


# ============================================================================
# User Usage and Action Endpoints
# ============================================================================

@router.get("/me/usage", response_model=UsageResponse, status_code=status.HTTP_200_OK)
async def get_user_usage(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """
    Get current user's quota and usage statistics.

    **Authentication**: Required (Bearer token)

    **Returns:**
    - Current quota information (daily limit, used, remaining, reset date)
    - Usage history (total, this month, this week, today)
    - Breakdown by action type
    """
    # Calculate quota info
    remaining_today = current_user.ai_action_quota_daily - current_user.ai_action_count_today

    quota = UsageQuota(
        daily_limit=current_user.ai_action_quota_daily,
        used_today=current_user.ai_action_count_today,
        remaining_today=remaining_today,
        reset_date=str(current_user.quota_reset_date),
        is_premium=current_user.is_premium
    )

    # Calculate usage history
    total_actions = session.exec(
        select(func.count()).select_from(AIAction).where(AIAction.user_id == current_user.id)
    ).one()

    # This month
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    actions_this_month = session.exec(
        select(func.count()).select_from(AIAction)
        .where(and_(AIAction.user_id == current_user.id, AIAction.created_at >= month_start))
    ).one()

    # This week
    week_start = datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    actions_this_week = session.exec(
        select(func.count()).select_from(AIAction)
        .where(and_(AIAction.user_id == current_user.id, AIAction.created_at >= week_start))
    ).one()

    usage_history = UsageHistory(
        total_actions=total_actions,
        this_month=actions_this_month,
        this_week=actions_this_week,
        today=current_user.ai_action_count_today
    )

    # Breakdown by type
    breakdown_query = select(AIAction.action_type, func.count(AIAction.id)).where(
        AIAction.user_id == current_user.id
    ).group_by(AIAction.action_type)

    breakdown_results = session.exec(breakdown_query).all()
    breakdown_by_type = {action_type: count for action_type, count in breakdown_results}

    return UsageResponse(
        quota=quota,
        usage_history=usage_history,
        breakdown_by_type=breakdown_by_type
    )


@router.get("/me/actions", response_model=UserActionList, status_code=status.HTTP_200_OK)
async def list_user_actions(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    action_type: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """
    List current user's AI actions.

    **Authentication**: Required (Bearer token)

    **Query Parameters:**
    - `skip`: Number of records to skip (default: 0)
    - `limit`: Maximum records to return (default: 20, max: 100)
    - `action_type`: Filter by action type
    - `status`: Filter by status
    - `date_from`: Filter by start date (ISO format)
    - `date_to`: Filter by end date (ISO format)

    **Returns:**
    - List of user's AI actions with pagination
    """
    # Build query
    query = select(AIAction).where(AIAction.user_id == current_user.id)

    # Apply filters
    filters = [AIAction.user_id == current_user.id]

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

    query = query.where(and_(*filters))

    # Get total count
    count_query = select(func.count()).select_from(AIAction).where(and_(*filters))
    total = session.exec(count_query).one()

    # Apply pagination and ordering
    query = query.order_by(AIAction.created_at.desc()).offset(skip).limit(limit)

    # Execute query
    actions = session.exec(query).all()

    # Build response
    action_items = []
    for action in actions:
        action_items.append(UserActionListItem(
            action_id=action.action_id,
            action_type=action.action_type,
            status=action.status,
            transcription_id=action.transcription_id,
            quota_cost=action.quota_cost,
            created_at=action.created_at,
            completed_at=action.completed_at
        ))

    return UserActionList(
        actions=action_items,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/me/actions/{action_id}", response_model=ActionDetailResponse, status_code=status.HTTP_200_OK)
async def get_user_action(
    action_id: str,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """
    Get specific action result.

    **Authentication**: Required (Bearer token)

    **Returns:**
    - Complete action details including result data
    """
    # Find action by action_id
    action = session.exec(
        select(AIAction).where(
            and_(
                AIAction.action_id == action_id,
                AIAction.user_id == current_user.id
            )
        )
    ).first()

    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action not found: {action_id}"
        )

    # Parse result_data and request_params if they exist
    import json
    result = None
    if action.result_data:
        try:
            result = json.loads(action.result_data)
        except json.JSONDecodeError:
            result = None

    # Build message
    message = f"endpoint {action.action_type} - work in progress to implement this functionality"
    if action.error_message:
        message = action.error_message

    return ActionDetailResponse(
        action_id=action.action_id,
        action_type=action.action_type,
        status=action.status,
        message=message,
        transcription_id=action.transcription_id,
        quota_cost=action.quota_cost,
        created_at=action.created_at,
        completed_at=action.completed_at,
        result=result,
        error=action.error_message
    )
