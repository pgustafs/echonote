"""
Service layer for SavedContent operations.

Handles business logic for creating, retrieving, updating, and deleting
saved AI-generated content.
"""

import logging
from datetime import datetime
from typing import Optional
from fastapi import HTTPException
from sqlmodel import Session, select

from backend.models import SavedContent, SavedContentCreate, SavedContentUpdate, SavedContentPublic, User

logger = logging.getLogger(__name__)


class SavedContentService:
    """Service class for SavedContent business logic"""

    @staticmethod
    def create_saved_content(
        session: Session,
        content_data: SavedContentCreate,
        user: User
    ) -> SavedContent:
        """
        Create new saved content.

        Args:
            session: Database session
            content_data: Content creation data
            user: Current authenticated user

        Returns:
            Created saved content

        Raises:
            HTTPException: If validation fails
        """
        logger.info(f"Creating saved content for user {user.id}, transcription {content_data.transcription_id}")

        # Verify user owns the transcription
        from backend.services.transcription_service import TranscriptionService
        transcription = TranscriptionService.get_transcription_by_id(
            session, content_data.transcription_id, user
        )

        # Create saved content
        saved_content = SavedContent(
            content_type=content_data.content_type,
            title=content_data.title,
            content=content_data.content,
            transcription_id=content_data.transcription_id,
            ai_action_id=content_data.ai_action_id,
            user_id=user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        session.add(saved_content)
        session.commit()
        session.refresh(saved_content)

        logger.info(f"Created saved content {saved_content.id}")
        return saved_content

    @staticmethod
    def get_saved_content_by_id(
        session: Session,
        content_id: int,
        user: User
    ) -> SavedContent:
        """
        Get saved content by ID.

        Args:
            session: Database session
            content_id: Saved content ID
            user: Current authenticated user

        Returns:
            Saved content

        Raises:
            HTTPException: If not found or permission denied
        """
        statement = select(SavedContent).where(
            SavedContent.id == content_id,
            SavedContent.user_id == user.id
        )
        saved_content = session.exec(statement).first()

        if not saved_content:
            logger.warning(f"Saved content {content_id} not found for user {user.id}")
            raise HTTPException(status_code=404, detail="Saved content not found")

        return saved_content

    @staticmethod
    def get_user_saved_content(
        session: Session,
        user: User,
        transcription_id: Optional[int] = None,
        content_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[SavedContent], int]:
        """
        Get list of saved content for user with optional filtering.

        Args:
            session: Database session
            user: Current authenticated user
            transcription_id: Optional filter by transcription
            content_type: Optional filter by content type
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (saved content list, total count)
        """
        # Build query
        statement = select(SavedContent).where(SavedContent.user_id == user.id)

        if transcription_id:
            statement = statement.where(SavedContent.transcription_id == transcription_id)

        if content_type:
            statement = statement.where(SavedContent.content_type == content_type)

        # Get total count
        count_statement = select(SavedContent).where(SavedContent.user_id == user.id)
        if transcription_id:
            count_statement = count_statement.where(SavedContent.transcription_id == transcription_id)
        if content_type:
            count_statement = count_statement.where(SavedContent.content_type == content_type)

        total = len(session.exec(count_statement).all())

        # Get paginated results, ordered by updated_at desc
        statement = statement.order_by(SavedContent.updated_at.desc())
        statement = statement.offset(skip).limit(limit)

        saved_content = session.exec(statement).all()

        logger.info(f"Retrieved {len(saved_content)} saved content items for user {user.id} (total: {total})")
        return list(saved_content), total

    @staticmethod
    def update_saved_content(
        session: Session,
        content_id: int,
        update_data: SavedContentUpdate,
        user: User
    ) -> SavedContent:
        """
        Update saved content.

        Args:
            session: Database session
            content_id: Saved content ID
            update_data: Update data
            user: Current authenticated user

        Returns:
            Updated saved content

        Raises:
            HTTPException: If not found or permission denied
        """
        saved_content = SavedContentService.get_saved_content_by_id(session, content_id, user)

        # Update fields
        if update_data.title is not None:
            saved_content.title = update_data.title

        if update_data.content is not None:
            saved_content.content = update_data.content

        # Update timestamp
        saved_content.updated_at = datetime.utcnow()

        session.add(saved_content)
        session.commit()
        session.refresh(saved_content)

        logger.info(f"Updated saved content {content_id}")
        return saved_content

    @staticmethod
    def delete_saved_content(
        session: Session,
        content_id: int,
        user: User
    ) -> None:
        """
        Delete saved content.

        Args:
            session: Database session
            content_id: Saved content ID
            user: Current authenticated user

        Raises:
            HTTPException: If not found or permission denied
        """
        saved_content = SavedContentService.get_saved_content_by_id(session, content_id, user)

        session.delete(saved_content)
        session.commit()

        logger.info(f"Deleted saved content {content_id}")

    @staticmethod
    def to_public_schema(saved_content: SavedContent) -> SavedContentPublic:
        """
        Convert database model to public API schema.

        Args:
            saved_content: Database saved content record

        Returns:
            Public schema
        """
        return SavedContentPublic(
            id=saved_content.id,
            content_type=saved_content.content_type,
            title=saved_content.title,
            content=saved_content.content,
            created_at=saved_content.created_at,
            updated_at=saved_content.updated_at,
            transcription_id=saved_content.transcription_id,
            ai_action_id=saved_content.ai_action_id
        )
