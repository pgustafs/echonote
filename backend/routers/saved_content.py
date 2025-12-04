"""
API router for SavedContent endpoints.

Provides CRUD operations for saved AI-generated content.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from backend.database import get_session
from backend.models import (
    User,
    SavedContent,
    SavedContentCreate,
    SavedContentUpdate,
    SavedContentPublic
)
from backend.auth import get_current_active_user
from backend.services.saved_content_service import SavedContentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/saved-content", tags=["saved-content"])


# ============================================================================
# Response Models
# ============================================================================

class SavedContentList:
    """Response model for list of saved content"""
    saved_content: list[SavedContentPublic]
    total: int
    skip: int
    limit: int


# ============================================================================
# Endpoints
# ============================================================================

@router.post("", response_model=SavedContentPublic, status_code=201)
def create_saved_content(
    content_data: SavedContentCreate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """
    Create new saved content.

    Creates a saved copy of AI-generated content that the user can
    edit and potentially publish later.

    **Authentication required**

    Args:
        content_data: Content creation data
        current_user: Authenticated user
        session: Database session

    Returns:
        Created saved content

    Raises:
        404: If transcription not found
        401: If not authenticated
        403: If user doesn't own the transcription
    """
    logger.info(f"User {current_user.id} creating saved content for transcription {content_data.transcription_id}")

    saved_content = SavedContentService.create_saved_content(
        session, content_data, current_user
    )

    return SavedContentService.to_public_schema(saved_content)


@router.get("", response_model=dict)
def list_saved_content(
    transcription_id: Optional[int] = None,
    content_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """
    List saved content with optional filtering.

    **Authentication required**

    Query parameters:
        transcription_id: Filter by transcription
        content_type: Filter by content type
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return

    Returns:
        List of saved content with pagination info

    Raises:
        401: If not authenticated
    """
    logger.info(
        f"User {current_user.id} listing saved content "
        f"(transcription_id={transcription_id}, content_type={content_type}, skip={skip}, limit={limit})"
    )

    saved_content, total = SavedContentService.get_user_saved_content(
        session,
        current_user,
        transcription_id=transcription_id,
        content_type=content_type,
        skip=skip,
        limit=limit
    )

    return {
        "saved_content": [SavedContentService.to_public_schema(sc) for sc in saved_content],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{content_id}", response_model=SavedContentPublic)
def get_saved_content(
    content_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """
    Get saved content by ID.

    **Authentication required**

    Args:
        content_id: Saved content ID
        current_user: Authenticated user
        session: Database session

    Returns:
        Saved content

    Raises:
        404: If not found
        401: If not authenticated
        403: If user doesn't own the content
    """
    logger.info(f"User {current_user.id} retrieving saved content {content_id}")

    saved_content = SavedContentService.get_saved_content_by_id(
        session, content_id, current_user
    )

    return SavedContentService.to_public_schema(saved_content)


@router.patch("/{content_id}", response_model=SavedContentPublic)
def update_saved_content(
    content_id: int,
    update_data: SavedContentUpdate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """
    Update saved content.

    Allows editing the title and/or content of saved content.

    **Authentication required**

    Args:
        content_id: Saved content ID
        update_data: Update data
        current_user: Authenticated user
        session: Database session

    Returns:
        Updated saved content

    Raises:
        404: If not found
        401: If not authenticated
        403: If user doesn't own the content
    """
    logger.info(f"User {current_user.id} updating saved content {content_id}")

    saved_content = SavedContentService.update_saved_content(
        session, content_id, update_data, current_user
    )

    return SavedContentService.to_public_schema(saved_content)


@router.delete("/{content_id}", status_code=204)
def delete_saved_content(
    content_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """
    Delete saved content.

    **Authentication required**

    Args:
        content_id: Saved content ID
        current_user: Authenticated user
        session: Database session

    Returns:
        No content (204)

    Raises:
        404: If not found
        401: If not authenticated
        403: If user doesn't own the content
    """
    logger.info(f"User {current_user.id} deleting saved content {content_id}")

    SavedContentService.delete_saved_content(session, content_id, current_user)

    return None
