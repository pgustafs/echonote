"""
Authentication routes for EchoNote.

Provides endpoints for user registration, login, and user management.
"""

import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

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
from backend.models import Token, User, UserCreate, UserLogin, UserPublic
from backend.logging_config import get_logger, get_security_logger

logger = get_logger(__name__)
security_logger = get_security_logger()

router = APIRouter(prefix="/api/auth", tags=["authentication"])


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
