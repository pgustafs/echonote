"""
AI Action Service - Business logic for AI-powered operations on transcriptions.

This service handles:
- Creating AI action records
- Retrieving and listing user actions
- Verifying transcription access
- Calculating action statistics
"""

import json
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status
from sqlmodel import Session, select, func

from backend.models import AIAction, AIActionPublic, Transcription, User
from backend.logging_config import get_logger
from backend.services.permission_service import PermissionService
from backend.services.llama_agent_service import LlamaAgentService
from backend.services.ai_action_prompts import get_prompts

logger = get_logger(__name__)


class AIActionService:
    """Service for managing AI actions on transcriptions"""

    @staticmethod
    def create_action_record(
        session: Session,
        user: User,
        transcription_id: int,
        action_type: str,
        request_params: dict,
        quota_cost: int
    ) -> AIAction:
        """
        Create a new AI action record in the database.

        Args:
            session: Database session
            user: User requesting the action
            transcription_id: ID of the transcription to process
            action_type: Type of AI action (e.g., 'analyze', 'create/linkedin-post')
            request_params: Dictionary of request parameters
            quota_cost: Quota cost for this action

        Returns:
            AIAction: Created action record with generated action_id
        """
        # Create AI action record
        ai_action = AIAction(
            user_id=user.id,
            transcription_id=transcription_id,
            action_type=action_type,
            status="work_in_progress",
            request_params=json.dumps(request_params),
            quota_cost=quota_cost,
            created_at=datetime.utcnow()
        )

        session.add(ai_action)
        session.commit()
        session.refresh(ai_action)

        # Increment user's quota usage
        PermissionService.increment_usage(
            session=session,
            user=user,
            action_type=action_type,
            quota_cost=quota_cost
        )

        logger.info(
            f"AI action created",
            extra={
                "action_id": ai_action.action_id,
                "user_id": user.id,
                "action_type": action_type,
                "transcription_id": transcription_id,
                "quota_cost": quota_cost
            }
        )

        return ai_action

    @staticmethod
    async def execute_ai_action(
        session: Session,
        ai_action: AIAction,
        transcription: Transcription,
        user: User
    ) -> AIAction:
        """
        Execute an AI action using LlamaStack agent.

        This method:
        1. Gets the appropriate prompts for the action type
        2. Creates a LlamaAgent instance with proper context
        3. Executes the action asynchronously
        4. Updates the AIAction record with the result

        Args:
            session: Database session
            ai_action: The AI action record to execute
            transcription: The transcription to process
            user: The user requesting the action

        Returns:
            AIAction: Updated action record with result

        Raises:
            Exception: If LlamaStack is not configured or execution fails
        """
        try:
            # Get system and user prompts for this action type
            system_prompt, user_prompt = get_prompts(
                ai_action.action_type,
                transcription.text or ""
            )

            # Create LlamaAgent service with proper context for auditing
            agent_service = LlamaAgentService(
                user_id=user.id,
                transcription_id=transcription.id,
                action_type=ai_action.action_type
            )

            logger.info(
                f"Executing AI action",
                extra={
                    "action_id": ai_action.action_id,
                    "user_id": user.id,
                    "transcription_id": transcription.id,
                    "action_type": ai_action.action_type
                }
            )

            # Execute the AI action asynchronously
            result_text = await agent_service.run(system_prompt, user_prompt)

            # Update the AI action record with the result
            ai_action.status = "completed"
            ai_action.result_data = json.dumps({"text": result_text})
            ai_action.completed_at = datetime.utcnow()
            ai_action.error_message = None

            session.add(ai_action)
            session.commit()
            session.refresh(ai_action)

            logger.info(
                f"AI action completed successfully",
                extra={
                    "action_id": ai_action.action_id,
                    "user_id": user.id,
                    "result_length": len(result_text)
                }
            )

            return ai_action

        except ValueError as e:
            # Unsupported action type or invalid configuration
            logger.error(
                f"AI action configuration error: {e}",
                extra={
                    "action_id": ai_action.action_id,
                    "action_type": ai_action.action_type
                }
            )
            ai_action.status = "failed"
            ai_action.error_message = str(e)
            ai_action.completed_at = datetime.utcnow()
            session.add(ai_action)
            session.commit()
            session.refresh(ai_action)
            raise

        except Exception as e:
            # Execution failed
            logger.error(
                f"AI action execution failed: {e}",
                extra={
                    "action_id": ai_action.action_id,
                    "action_type": ai_action.action_type,
                    "error": str(e)
                }
            )
            ai_action.status = "failed"
            ai_action.error_message = str(e)
            ai_action.completed_at = datetime.utcnow()
            session.add(ai_action)
            session.commit()
            session.refresh(ai_action)
            raise

    @staticmethod
    def get_user_actions(
        session: Session,
        user: User,
        skip: int = 0,
        limit: int = 20,
        action_type_filter: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> tuple[list[AIAction], int]:
        """
        Get user's AI actions with optional filters and pagination.

        Args:
            session: Database session
            user: User to get actions for
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            action_type_filter: Optional filter by action type
            status_filter: Optional filter by status

        Returns:
            Tuple of (actions list, total count)
        """
        # Build query
        query = select(AIAction).where(AIAction.user_id == user.id)

        # Apply filters
        if action_type_filter:
            query = query.where(AIAction.action_type == action_type_filter)
        if status_filter:
            query = query.where(AIAction.status == status_filter)

        # Get total count
        count_query = select(func.count()).select_from(AIAction).where(AIAction.user_id == user.id)
        if action_type_filter:
            count_query = count_query.where(AIAction.action_type == action_type_filter)
        if status_filter:
            count_query = count_query.where(AIAction.status == status_filter)
        total = session.exec(count_query).one()

        # Get paginated results
        query = query.order_by(AIAction.created_at.desc()).offset(skip).limit(limit)
        actions = session.exec(query).all()

        return actions, total

    @staticmethod
    def get_action_by_id(session: Session, action_id: str, user: User) -> AIAction:
        """
        Get a specific AI action by action_id, verifying user ownership.

        Args:
            session: Database session
            action_id: Unique action identifier (UUID)
            user: User requesting the action

        Returns:
            AIAction: The requested action

        Raises:
            HTTPException: 404 if action not found, 403 if user doesn't own it
        """
        # Find action by action_id
        statement = select(AIAction).where(AIAction.action_id == action_id)
        action = session.exec(statement).first()

        if not action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AI action not found: {action_id}"
            )

        # Verify ownership
        if action.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this AI action"
            )

        return action

    @staticmethod
    def verify_transcription_access(
        session: Session,
        transcription_id: int,
        user: User
    ) -> Transcription:
        """
        Verify that a transcription exists and the user owns it.

        Args:
            session: Database session
            transcription_id: ID of the transcription
            user: User requesting access

        Returns:
            Transcription: The verified transcription

        Raises:
            HTTPException: 404 if not found, 403 if user doesn't own it
        """
        # Find transcription
        transcription = session.get(Transcription, transcription_id)

        if not transcription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transcription not found: {transcription_id}"
            )

        # Verify ownership
        if transcription.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this transcription"
            )

        return transcription

    @staticmethod
    def get_action_statistics(session: Session, user: User) -> dict:
        """
        Get user's AI action usage statistics.

        Args:
            session: Database session
            user: User to get statistics for

        Returns:
            Dictionary with action statistics grouped by type and status
        """
        # Get total actions
        total_query = select(func.count()).select_from(AIAction).where(AIAction.user_id == user.id)
        total_actions = session.exec(total_query).one()

        # Get actions this month
        first_day_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_query = select(func.count()).select_from(AIAction).where(
            AIAction.user_id == user.id,
            AIAction.created_at >= first_day_of_month
        )
        actions_this_month = session.exec(month_query).one()

        # Get actions this week
        start_of_week = datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        week_query = select(func.count()).select_from(AIAction).where(
            AIAction.user_id == user.id,
            AIAction.created_at >= start_of_week
        )
        actions_this_week = session.exec(week_query).one()

        # Get actions today
        start_of_day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_query = select(func.count()).select_from(AIAction).where(
            AIAction.user_id == user.id,
            AIAction.created_at >= start_of_day
        )
        actions_today = session.exec(today_query).one()

        # Get breakdown by action type
        type_query = select(
            AIAction.action_type,
            func.count(AIAction.id).label('count')
        ).where(
            AIAction.user_id == user.id
        ).group_by(AIAction.action_type)
        type_results = session.exec(type_query).all()
        breakdown_by_type = {row.action_type: row.count for row in type_results}

        return {
            "total_actions": total_actions,
            "this_month": actions_this_month,
            "this_week": actions_this_week,
            "today": actions_today,
            "breakdown_by_type": breakdown_by_type
        }
