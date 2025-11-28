"""
AI Actions Router - API endpoints for AI-powered transcription operations.

This router provides 18 AI action endpoints across 5 categories:
- Analyze: Summarize, extract tasks, identify next actions
- Create: Generate content (LinkedIn posts, emails, blog posts, captions)
- Improve: Transform text (summarize, rewrite, expand, shorten)
- Translate: Convert to different languages
- Voice: Clean up speech-to-text output

All endpoints return standardized "work in progress" responses until implemented.
"""

import json
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlmodel import Session

from backend.auth import get_current_active_user
from backend.database import get_session
from backend.models import User, AIActionRequest, AIActionResponse, ImproveActionRequest, ChatRequest
from backend.services.ai_action_service import AIActionService
from backend.services.permission_service import PermissionService
from backend.services.llama_agent_service import LlamaAgentService
from backend.services.ai_action_prompts import get_improve_prompts, get_chat_prompts
from backend.middleware.quota_checker import require_quota, track_usage
from backend.middleware.rate_limiter import ai_action_rate_limit
from backend.logging_config import get_logger, get_security_logger

logger = get_logger(__name__)
security_logger = get_security_logger()

router = APIRouter(
    prefix="/api/v1/actions",
    tags=["AI Actions"],
    dependencies=[Depends(get_current_active_user)]
)


def create_dummy_response(
    action_type: str,
    action_id: str,
    user: User,
    quota_cost: int,
    transcription_text: str
) -> AIActionResponse:
    """
    Create standardized work-in-progress response for AI action endpoints.

    Args:
        action_type: Type of AI action (e.g., 'analyze', 'create/linkedin-post')
        action_id: Unique identifier for this action (UUID)
        user: User who requested the action
        quota_cost: Quota cost for this action
        transcription_text: The text of the transcription being processed

    Returns:
        AIActionResponse with work-in-progress status and quota information
    """
    # Calculate quota remaining (user.ai_action_count_today is already incremented by create_action_record)
    quota_remaining = user.ai_action_quota_daily - user.ai_action_count_today

    # Calculate next reset date
    if user.quota_reset_date >= datetime.utcnow().date():
        next_reset = user.quota_reset_date + timedelta(days=1)
    else:
        next_reset = datetime.utcnow().date() + timedelta(days=1)

    return AIActionResponse(
        action_id=action_id,
        status="work_in_progress",
        message=f"endpoint {action_type} - work in progress to implement this functionality\n\nTranscription text: {transcription_text}",
        quota_remaining=quota_remaining,
        quota_reset_date=str(next_reset),
        result=None,
        error=None,
        created_at=datetime.utcnow(),
        completed_at=None
    )


# ============================================================================
# Category 1: Analyze
# ============================================================================

@router.post("/analyze", response_model=AIActionResponse, status_code=status.HTTP_200_OK)
@ai_action_rate_limit()
@require_quota(cost=1)
@track_usage(action_type="analyze")
async def analyze_transcription(
    request: Request,
    response: Response,
    action_request: AIActionRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Analyze transcription to extract summary, tasks, and next actions.

    **Rate Limit**: 30 requests per minute per user
    **Quota Cost:** 1 action

    **Request Parameters:**
    - `transcription_id`: ID of the transcription to analyze
    - `options.analysis_type`: Type of analysis ("summary", "tasks", "next_actions", "all")
    - `options.detail_level`: Level of detail ("brief", "concise", "detailed")

    **Returns:**
    - Actual AI-generated analysis with quota information
    """
    # Verify transcription exists and user owns it
    transcription = AIActionService.verify_transcription_access(session, action_request.transcription_id, current_user)

    # Create AI action record
    ai_action = AIActionService.create_action_record(
        session=session,
        user=current_user,
        transcription_id=action_request.transcription_id,
        action_type="analyze",
        request_params=action_request.options,
        quota_cost=1
    )

    # Execute AI action asynchronously
    ai_action = await AIActionService.execute_ai_action(
        session=session,
        ai_action=ai_action,
        transcription=transcription,
        user=current_user
    )

    # Calculate quota remaining
    quota_remaining = current_user.ai_action_quota_daily - current_user.ai_action_count_today

    # Return response with actual result
    return AIActionResponse(
        action_id=ai_action.action_id,
        status=ai_action.status,
        message=json.loads(ai_action.result_data).get("text") if ai_action.result_data else None,
        quota_remaining=quota_remaining,
        quota_reset_date=str(current_user.quota_reset_date),
        result=json.loads(ai_action.result_data) if ai_action.result_data else None,
        error=ai_action.error_message,
        created_at=ai_action.created_at,
        completed_at=ai_action.completed_at,
        session_id=json.loads(ai_action.result_data).get("session_id") if ai_action.result_data else None
    )


# ============================================================================
# Category 2: Create
# ============================================================================

@router.post("/create/linkedin-post", response_model=AIActionResponse, status_code=status.HTTP_200_OK)
@require_quota(cost=2)
@track_usage(action_type="create/linkedin-post")
async def create_linkedin_post(
    action_request: AIActionRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate a LinkedIn post from transcription.

    **Quota Cost:** 2 actions

    **Request Parameters:**
    - `transcription_id`: ID of the transcription to process
    - `options.tone`: Tone of the post ("professional", "casual", "inspirational")
    - `options.include_hashtags`: Whether to include hashtags (boolean)
    - `options.max_length`: Maximum length in characters (default: 3000)

    **Returns:**
    - Actual AI-generated LinkedIn post with quota information
    """
    transcription = AIActionService.verify_transcription_access(session, action_request.transcription_id, current_user)

    ai_action = AIActionService.create_action_record(
        session=session,
        user=current_user,
        transcription_id=action_request.transcription_id,
        action_type="create-linkedin-post",
        request_params=action_request.options,
        quota_cost=2
    )

    # Execute AI action
    ai_action = await AIActionService.execute_ai_action(
        session=session,
        ai_action=ai_action,
        transcription=transcription,
        user=current_user
    )

    quota_remaining = current_user.ai_action_quota_daily - current_user.ai_action_count_today

    return AIActionResponse(
        action_id=ai_action.action_id,
        status=ai_action.status,
        message=json.loads(ai_action.result_data).get("text") if ai_action.result_data else None,
        quota_remaining=quota_remaining,
        quota_reset_date=str(current_user.quota_reset_date),
        result=json.loads(ai_action.result_data) if ai_action.result_data else None,
        error=ai_action.error_message,
        created_at=ai_action.created_at,
        completed_at=ai_action.completed_at,
        session_id=json.loads(ai_action.result_data).get("session_id") if ai_action.result_data else None
    )


@router.post("/create/email-draft", response_model=AIActionResponse, status_code=status.HTTP_200_OK)
@require_quota(cost=2)
@track_usage(action_type="create/email-draft")
async def create_email_draft(
    action_request: AIActionRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate an email draft from transcription.

    **Quota Cost:** 2 actions

    **Request Parameters:**
    - `transcription_id`: ID of the transcription to process
    - `options.tone`: Tone of the email ("formal", "casual", "friendly")
    - `options.include_subject`: Whether to include subject line (boolean)
    - `options.recipient_context`: Optional context about the recipient

    **Returns:**
    - Actual AI-generated email draft with quota information
    """
    transcription = AIActionService.verify_transcription_access(session, action_request.transcription_id, current_user)

    ai_action = AIActionService.create_action_record(
        session=session,
        user=current_user,
        transcription_id=action_request.transcription_id,
        action_type="create/email-draft",
        request_params=action_request.options,
        quota_cost=2
    )

    # Execute AI action
    ai_action = await AIActionService.execute_ai_action(
        session=session,
        ai_action=ai_action,
        transcription=transcription,
        user=current_user
    )

    quota_remaining = current_user.ai_action_quota_daily - current_user.ai_action_count_today

    return AIActionResponse(
        action_id=ai_action.action_id,
        status=ai_action.status,
        message=json.loads(ai_action.result_data).get("text") if ai_action.result_data else None,
        quota_remaining=quota_remaining,
        quota_reset_date=str(current_user.quota_reset_date),
        result=json.loads(ai_action.result_data) if ai_action.result_data else None,
        error=ai_action.error_message,
        created_at=ai_action.created_at,
        completed_at=ai_action.completed_at,
        session_id=json.loads(ai_action.result_data).get("session_id") if ai_action.result_data else None
    )


@router.post("/create/blog-post", response_model=AIActionResponse, status_code=status.HTTP_200_OK)
@require_quota(cost=2)
@track_usage(action_type="create/blog-post")
async def create_blog_post(
    action_request: AIActionRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate a blog post from transcription.

    **Quota Cost:** 2 actions

    **Request Parameters:**
    - `transcription_id`: ID of the transcription to process
    - `options.style`: Writing style ("informative", "conversational", "technical")
    - `options.include_outline`: Whether to include an outline (boolean)
    - `options.target_length`: Target length ("short", "medium", "long")

    **Returns:**
    - Actual AI-generated blog post with quota information
    """
    transcription = AIActionService.verify_transcription_access(session, action_request.transcription_id, current_user)

    ai_action = AIActionService.create_action_record(
        session=session,
        user=current_user,
        transcription_id=action_request.transcription_id,
        action_type="create/blog-post",
        request_params=action_request.options,
        quota_cost=2
    )

    # Execute AI action
    ai_action = await AIActionService.execute_ai_action(
        session=session,
        ai_action=ai_action,
        transcription=transcription,
        user=current_user
    )

    quota_remaining = current_user.ai_action_quota_daily - current_user.ai_action_count_today

    return AIActionResponse(
        action_id=ai_action.action_id,
        status=ai_action.status,
        message=json.loads(ai_action.result_data).get("text") if ai_action.result_data else None,
        quota_remaining=quota_remaining,
        quota_reset_date=str(current_user.quota_reset_date),
        result=json.loads(ai_action.result_data) if ai_action.result_data else None,
        error=ai_action.error_message,
        created_at=ai_action.created_at,
        completed_at=ai_action.completed_at,
        session_id=json.loads(ai_action.result_data).get("session_id") if ai_action.result_data else None
    )


@router.post("/create/social-media-caption", response_model=AIActionResponse, status_code=status.HTTP_200_OK)
@require_quota(cost=2)
@track_usage(action_type="create/social-media-caption")
async def create_social_media_caption(
    action_request: AIActionRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate a social media caption from transcription.

    **Quota Cost:** 2 actions

    **Request Parameters:**
    - `transcription_id`: ID of the transcription to process
    - `options.platform`: Platform ("instagram", "twitter", "facebook")
    - `options.include_emojis`: Whether to include emojis (boolean)
    - `options.include_hashtags`: Whether to include hashtags (boolean)
    - `options.max_length`: Maximum length in characters

    **Returns:**
    - Actual AI-generated social media caption with quota information
    """
    transcription = AIActionService.verify_transcription_access(session, action_request.transcription_id, current_user)

    ai_action = AIActionService.create_action_record(
        session=session,
        user=current_user,
        transcription_id=action_request.transcription_id,
        action_type="create/social-media-caption",
        request_params=action_request.options,
        quota_cost=2
    )

    # Execute AI action
    ai_action = await AIActionService.execute_ai_action(
        session=session,
        ai_action=ai_action,
        transcription=transcription,
        user=current_user
    )

    quota_remaining = current_user.ai_action_quota_daily - current_user.ai_action_count_today

    return AIActionResponse(
        action_id=ai_action.action_id,
        status=ai_action.status,
        message=json.loads(ai_action.result_data).get("text") if ai_action.result_data else None,
        quota_remaining=quota_remaining,
        quota_reset_date=str(current_user.quota_reset_date),
        result=json.loads(ai_action.result_data) if ai_action.result_data else None,
        error=ai_action.error_message,
        created_at=ai_action.created_at,
        completed_at=ai_action.completed_at,
        session_id=json.loads(ai_action.result_data).get("session_id") if ai_action.result_data else None
    )


# ============================================================================
# Category 3: Improve/Transform
# ============================================================================

@router.post("/improve/summarize", response_model=AIActionResponse, status_code=status.HTTP_200_OK)
@require_quota(cost=1)
@track_usage(action_type="improve/summarize")
async def summarize_transcription(
    action_request: AIActionRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a concise summary of the transcription.

    **Quota Cost:** 1 action

    **Request Parameters:**
    - `transcription_id`: ID of the transcription to process
    - `options.length`: Summary length ("brief", "medium", "detailed")
    - `options.format`: Output format ("paragraph", "bullets")

    **Returns:**
    - Actual AI-generated summary with quota information
    """
    transcription = AIActionService.verify_transcription_access(session, action_request.transcription_id, current_user)

    ai_action = AIActionService.create_action_record(
        session=session,
        user=current_user,
        transcription_id=action_request.transcription_id,
        action_type="improve/summarize",
        request_params=action_request.options,
        quota_cost=1
    )

    # Execute AI action
    ai_action = await AIActionService.execute_ai_action(
        session=session,
        ai_action=ai_action,
        transcription=transcription,
        user=current_user
    )

    quota_remaining = current_user.ai_action_quota_daily - current_user.ai_action_count_today

    return AIActionResponse(
        action_id=ai_action.action_id,
        status=ai_action.status,
        message=json.loads(ai_action.result_data).get("text") if ai_action.result_data else None,
        quota_remaining=quota_remaining,
        quota_reset_date=str(current_user.quota_reset_date),
        result=json.loads(ai_action.result_data) if ai_action.result_data else None,
        error=ai_action.error_message,
        created_at=ai_action.created_at,
        completed_at=ai_action.completed_at,
        session_id=json.loads(ai_action.result_data).get("session_id") if ai_action.result_data else None
    )


@router.post("/improve/summarize-bullets", response_model=AIActionResponse, status_code=status.HTTP_200_OK)
@require_quota(cost=1)
@track_usage(action_type="improve/summarize-bullets")
async def summarize_bullets(
    action_request: AIActionRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a bullet-point summary of the transcription.

    **Quota Cost:** 1 action

    **Request Parameters:**
    - `transcription_id`: ID of the transcription to process
    - `options.max_bullets`: Maximum number of bullet points (default: 5)
    - `options.detail_level`: Detail level ("concise", "detailed")

    **Returns:**
    - Actual AI-generated bullet-point summary with quota information
    """
    transcription = AIActionService.verify_transcription_access(session, action_request.transcription_id, current_user)

    ai_action = AIActionService.create_action_record(
        session=session,
        user=current_user,
        transcription_id=action_request.transcription_id,
        action_type="improve/summarize-bullets",
        request_params=action_request.options,
        quota_cost=1
    )

    # Execute AI action
    ai_action = await AIActionService.execute_ai_action(
        session=session,
        ai_action=ai_action,
        transcription=transcription,
        user=current_user
    )

    quota_remaining = current_user.ai_action_quota_daily - current_user.ai_action_count_today

    return AIActionResponse(
        action_id=ai_action.action_id,
        status=ai_action.status,
        message=json.loads(ai_action.result_data).get("text") if ai_action.result_data else None,
        quota_remaining=quota_remaining,
        quota_reset_date=str(current_user.quota_reset_date),
        result=json.loads(ai_action.result_data) if ai_action.result_data else None,
        error=ai_action.error_message,
        created_at=ai_action.created_at,
        completed_at=ai_action.completed_at,
        session_id=json.loads(ai_action.result_data).get("session_id") if ai_action.result_data else None
    )


@router.post("/improve/rewrite-formal", response_model=AIActionResponse, status_code=status.HTTP_200_OK)
@require_quota(cost=1)
@track_usage(action_type="improve/rewrite-formal")
async def rewrite_formal(
    action_request: AIActionRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Rewrite the transcription in a formal tone.

    **Quota Cost:** 1 action

    **Request Parameters:**
    - `transcription_id`: ID of the transcription to process
    - `options.preserve_structure`: Whether to preserve original structure (boolean)

    **Returns:**
    - Actual AI-generated formal rewrite with quota information
    """
    transcription = AIActionService.verify_transcription_access(session, action_request.transcription_id, current_user)

    ai_action = AIActionService.create_action_record(
        session=session,
        user=current_user,
        transcription_id=action_request.transcription_id,
        action_type="improve/rewrite-formal",
        request_params=action_request.options,
        quota_cost=1
    )

    # Execute AI action
    ai_action = await AIActionService.execute_ai_action(
        session=session,
        ai_action=ai_action,
        transcription=transcription,
        user=current_user
    )

    quota_remaining = current_user.ai_action_quota_daily - current_user.ai_action_count_today

    return AIActionResponse(
        action_id=ai_action.action_id,
        status=ai_action.status,
        message=json.loads(ai_action.result_data).get("text") if ai_action.result_data else None,
        quota_remaining=quota_remaining,
        quota_reset_date=str(current_user.quota_reset_date),
        result=json.loads(ai_action.result_data) if ai_action.result_data else None,
        error=ai_action.error_message,
        created_at=ai_action.created_at,
        completed_at=ai_action.completed_at,
        session_id=json.loads(ai_action.result_data).get("session_id") if ai_action.result_data else None
    )


@router.post("/improve/rewrite-friendly", response_model=AIActionResponse, status_code=status.HTTP_200_OK)
@require_quota(cost=1)
@track_usage(action_type="improve/rewrite-friendly")
async def rewrite_friendly(
    action_request: AIActionRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Rewrite the transcription in a friendly, casual tone.

    **Quota Cost:** 1 action

    **Request Parameters:**
    - `transcription_id`: ID of the transcription to process
    - `options.preserve_structure`: Whether to preserve original structure (boolean)

    **Returns:**
    - Actual AI-generated friendly rewrite with quota information
    """
    transcription = AIActionService.verify_transcription_access(session, action_request.transcription_id, current_user)

    ai_action = AIActionService.create_action_record(
        session=session,
        user=current_user,
        transcription_id=action_request.transcription_id,
        action_type="improve/rewrite-friendly",
        request_params=action_request.options,
        quota_cost=1
    )

    # Execute AI action
    ai_action = await AIActionService.execute_ai_action(
        session=session,
        ai_action=ai_action,
        transcription=transcription,
        user=current_user
    )

    quota_remaining = current_user.ai_action_quota_daily - current_user.ai_action_count_today

    return AIActionResponse(
        action_id=ai_action.action_id,
        status=ai_action.status,
        message=json.loads(ai_action.result_data).get("text") if ai_action.result_data else None,
        quota_remaining=quota_remaining,
        quota_reset_date=str(current_user.quota_reset_date),
        result=json.loads(ai_action.result_data) if ai_action.result_data else None,
        error=ai_action.error_message,
        created_at=ai_action.created_at,
        completed_at=ai_action.completed_at,
        session_id=json.loads(ai_action.result_data).get("session_id") if ai_action.result_data else None
    )


@router.post("/improve/rewrite-simple", response_model=AIActionResponse, status_code=status.HTTP_200_OK)
@require_quota(cost=1)
@track_usage(action_type="improve/rewrite-simple")
async def rewrite_simple(
    action_request: AIActionRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Simplify the transcription for better accessibility.

    **Quota Cost:** 1 action

    **Request Parameters:**
    - `transcription_id`: ID of the transcription to process
    - `options.reading_level`: Target reading level (e.g., "grade_8")

    **Returns:**
    - Actual AI-generated simplified text with quota information
    """
    transcription = AIActionService.verify_transcription_access(session, action_request.transcription_id, current_user)

    ai_action = AIActionService.create_action_record(
        session=session,
        user=current_user,
        transcription_id=action_request.transcription_id,
        action_type="improve/rewrite-simple",
        request_params=action_request.options,
        quota_cost=1
    )

    # Execute AI action
    ai_action = await AIActionService.execute_ai_action(
        session=session,
        ai_action=ai_action,
        transcription=transcription,
        user=current_user
    )

    quota_remaining = current_user.ai_action_quota_daily - current_user.ai_action_count_today

    return AIActionResponse(
        action_id=ai_action.action_id,
        status=ai_action.status,
        message=json.loads(ai_action.result_data).get("text") if ai_action.result_data else None,
        quota_remaining=quota_remaining,
        quota_reset_date=str(current_user.quota_reset_date),
        result=json.loads(ai_action.result_data) if ai_action.result_data else None,
        error=ai_action.error_message,
        created_at=ai_action.created_at,
        completed_at=ai_action.completed_at,
        session_id=json.loads(ai_action.result_data).get("session_id") if ai_action.result_data else None
    )


@router.post("/improve/expand", response_model=AIActionResponse, status_code=status.HTTP_200_OK)
@require_quota(cost=1)
@track_usage(action_type="improve/expand")
async def expand_transcription(
    action_request: AIActionRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Expand the transcription with more detail and context.

    **Quota Cost:** 1 action

    **Request Parameters:**
    - `transcription_id`: ID of the transcription to process
    - `options.expansion_factor`: How much to expand (1.2 - 2.0)

    **Returns:**
    - Actual AI-generated expanded text with quota information
    """
    transcription = AIActionService.verify_transcription_access(session, action_request.transcription_id, current_user)

    ai_action = AIActionService.create_action_record(
        session=session,
        user=current_user,
        transcription_id=action_request.transcription_id,
        action_type="improve/expand",
        request_params=action_request.options,
        quota_cost=1
    )

    # Execute AI action
    ai_action = await AIActionService.execute_ai_action(
        session=session,
        ai_action=ai_action,
        transcription=transcription,
        user=current_user
    )

    quota_remaining = current_user.ai_action_quota_daily - current_user.ai_action_count_today

    return AIActionResponse(
        action_id=ai_action.action_id,
        status=ai_action.status,
        message=json.loads(ai_action.result_data).get("text") if ai_action.result_data else None,
        quota_remaining=quota_remaining,
        quota_reset_date=str(current_user.quota_reset_date),
        result=json.loads(ai_action.result_data) if ai_action.result_data else None,
        error=ai_action.error_message,
        created_at=ai_action.created_at,
        completed_at=ai_action.completed_at,
        session_id=json.loads(ai_action.result_data).get("session_id") if ai_action.result_data else None
    )


@router.post("/improve/shorten", response_model=AIActionResponse, status_code=status.HTTP_200_OK)
@require_quota(cost=1)
@track_usage(action_type="improve/shorten")
async def shorten_transcription(
    action_request: AIActionRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Condense the transcription while preserving key points.

    **Quota Cost:** 1 action

    **Request Parameters:**
    - `transcription_id`: ID of the transcription to process
    - `options.target_reduction`: Target reduction (0.3 - 0.7, where 0.5 = 50% of original)

    **Returns:**
    - Actual AI-generated shortened text with quota information
    """
    transcription = AIActionService.verify_transcription_access(session, action_request.transcription_id, current_user)

    ai_action = AIActionService.create_action_record(
        session=session,
        user=current_user,
        transcription_id=action_request.transcription_id,
        action_type="improve/shorten",
        request_params=action_request.options,
        quota_cost=1
    )

    # Execute AI action
    ai_action = await AIActionService.execute_ai_action(
        session=session,
        ai_action=ai_action,
        transcription=transcription,
        user=current_user
    )

    quota_remaining = current_user.ai_action_quota_daily - current_user.ai_action_count_today

    return AIActionResponse(
        action_id=ai_action.action_id,
        status=ai_action.status,
        message=json.loads(ai_action.result_data).get("text") if ai_action.result_data else None,
        quota_remaining=quota_remaining,
        quota_reset_date=str(current_user.quota_reset_date),
        result=json.loads(ai_action.result_data) if ai_action.result_data else None,
        error=ai_action.error_message,
        created_at=ai_action.created_at,
        completed_at=ai_action.completed_at,
        session_id=json.loads(ai_action.result_data).get("session_id") if ai_action.result_data else None
    )


# ============================================================================
# Category 4: Translate
# ============================================================================

@router.post("/translate/to-english", response_model=AIActionResponse, status_code=status.HTTP_200_OK)
@require_quota(cost=1)
@track_usage(action_type="translate/to-english")
async def translate_to_english(
    action_request: AIActionRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Translate the transcription to English.

    **Quota Cost:** 1 action

    **Request Parameters:**
    - `transcription_id`: ID of the transcription to process
    - `options.preserve_formatting`: Whether to preserve original formatting (boolean)

    **Returns:**
    - Actual AI-generated English translation with quota information
    """
    transcription = AIActionService.verify_transcription_access(session, action_request.transcription_id, current_user)

    ai_action = AIActionService.create_action_record(
        session=session,
        user=current_user,
        transcription_id=action_request.transcription_id,
        action_type="translate/to-english",
        request_params=action_request.options,
        quota_cost=1
    )

    # Execute AI action
    ai_action = await AIActionService.execute_ai_action(
        session=session,
        ai_action=ai_action,
        transcription=transcription,
        user=current_user
    )

    quota_remaining = current_user.ai_action_quota_daily - current_user.ai_action_count_today

    return AIActionResponse(
        action_id=ai_action.action_id,
        status=ai_action.status,
        message=json.loads(ai_action.result_data).get("text") if ai_action.result_data else None,
        quota_remaining=quota_remaining,
        quota_reset_date=str(current_user.quota_reset_date),
        result=json.loads(ai_action.result_data) if ai_action.result_data else None,
        error=ai_action.error_message,
        created_at=ai_action.created_at,
        completed_at=ai_action.completed_at,
        session_id=json.loads(ai_action.result_data).get("session_id") if ai_action.result_data else None
    )


@router.post("/translate/to-swedish", response_model=AIActionResponse, status_code=status.HTTP_200_OK)
@require_quota(cost=1)
@track_usage(action_type="translate/to-swedish")
async def translate_to_swedish(
    action_request: AIActionRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Translate the transcription to Swedish.

    **Quota Cost:** 1 action

    **Request Parameters:**
    - `transcription_id`: ID of the transcription to process
    - `options.preserve_formatting`: Whether to preserve original formatting (boolean)
    - `options.variant`: Swedish variant ("sweden", "finland")

    **Returns:**
    - Actual AI-generated Swedish translation with quota information
    """
    transcription = AIActionService.verify_transcription_access(session, action_request.transcription_id, current_user)

    ai_action = AIActionService.create_action_record(
        session=session,
        user=current_user,
        transcription_id=action_request.transcription_id,
        action_type="translate/to-swedish",
        request_params=action_request.options,
        quota_cost=1
    )

    # Execute AI action
    ai_action = await AIActionService.execute_ai_action(
        session=session,
        ai_action=ai_action,
        transcription=transcription,
        user=current_user
    )

    quota_remaining = current_user.ai_action_quota_daily - current_user.ai_action_count_today

    return AIActionResponse(
        action_id=ai_action.action_id,
        status=ai_action.status,
        message=json.loads(ai_action.result_data).get("text") if ai_action.result_data else None,
        quota_remaining=quota_remaining,
        quota_reset_date=str(current_user.quota_reset_date),
        result=json.loads(ai_action.result_data) if ai_action.result_data else None,
        error=ai_action.error_message,
        created_at=ai_action.created_at,
        completed_at=ai_action.completed_at,
        session_id=json.loads(ai_action.result_data).get("session_id") if ai_action.result_data else None
    )


@router.post("/translate/to-czech", response_model=AIActionResponse, status_code=status.HTTP_200_OK)
@require_quota(cost=1)
@track_usage(action_type="translate/to-czech")
async def translate_to_czech(
    action_request: AIActionRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Translate the transcription to Czech.

    **Quota Cost:** 1 action

    **Request Parameters:**
    - `transcription_id`: ID of the transcription to process
    - `options.preserve_formatting`: Whether to preserve original formatting (boolean)

    **Returns:**
    - Actual AI-generated Czech translation with quota information
    """
    transcription = AIActionService.verify_transcription_access(session, action_request.transcription_id, current_user)

    ai_action = AIActionService.create_action_record(
        session=session,
        user=current_user,
        transcription_id=action_request.transcription_id,
        action_type="translate/to-czech",
        request_params=action_request.options,
        quota_cost=1
    )

    # Execute AI action
    ai_action = await AIActionService.execute_ai_action(
        session=session,
        ai_action=ai_action,
        transcription=transcription,
        user=current_user
    )

    quota_remaining = current_user.ai_action_quota_daily - current_user.ai_action_count_today

    return AIActionResponse(
        action_id=ai_action.action_id,
        status=ai_action.status,
        message=json.loads(ai_action.result_data).get("text") if ai_action.result_data else None,
        quota_remaining=quota_remaining,
        quota_reset_date=str(current_user.quota_reset_date),
        result=json.loads(ai_action.result_data) if ai_action.result_data else None,
        error=ai_action.error_message,
        created_at=ai_action.created_at,
        completed_at=ai_action.completed_at,
        session_id=json.loads(ai_action.result_data).get("session_id") if ai_action.result_data else None
    )


# ============================================================================
# Category 5: Voice-Specific Utilities
# ============================================================================

@router.post("/voice/clean-filler-words", response_model=AIActionResponse, status_code=status.HTTP_200_OK)
@require_quota(cost=1)
@track_usage(action_type="voice/clean-filler-words")
async def clean_filler_words(
    action_request: AIActionRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Remove filler words (um, uh, like, etc.) from the transcription.

    **Quota Cost:** 1 action

    **Request Parameters:**
    - `transcription_id`: ID of the transcription to process
    - `options.aggressiveness`: How aggressively to remove fillers ("light", "moderate", "aggressive")

    **Returns:**
    - Actual AI-generated text with filler words removed and quota information
    """
    transcription = AIActionService.verify_transcription_access(session, action_request.transcription_id, current_user)

    ai_action = AIActionService.create_action_record(
        session=session,
        user=current_user,
        transcription_id=action_request.transcription_id,
        action_type="voice/clean-filler-words",
        request_params=action_request.options,
        quota_cost=1
    )

    # Execute AI action
    ai_action = await AIActionService.execute_ai_action(
        session=session,
        ai_action=ai_action,
        transcription=transcription,
        user=current_user
    )

    quota_remaining = current_user.ai_action_quota_daily - current_user.ai_action_count_today

    return AIActionResponse(
        action_id=ai_action.action_id,
        status=ai_action.status,
        message=json.loads(ai_action.result_data).get("text") if ai_action.result_data else None,
        quota_remaining=quota_remaining,
        quota_reset_date=str(current_user.quota_reset_date),
        result=json.loads(ai_action.result_data) if ai_action.result_data else None,
        error=ai_action.error_message,
        created_at=ai_action.created_at,
        completed_at=ai_action.completed_at,
        session_id=json.loads(ai_action.result_data).get("session_id") if ai_action.result_data else None
    )


@router.post("/voice/fix-grammar", response_model=AIActionResponse, status_code=status.HTTP_200_OK)
@require_quota(cost=1)
@track_usage(action_type="voice/fix-grammar")
async def fix_grammar(
    action_request: AIActionRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Correct grammatical errors in the transcription.

    **Quota Cost:** 1 action

    **Request Parameters:**
    - `transcription_id`: ID of the transcription to process
    - `options.preserve_style`: Whether to preserve speaking style (boolean)

    **Returns:**
    - Actual AI-generated grammatically corrected text with quota information
    """
    transcription = AIActionService.verify_transcription_access(session, action_request.transcription_id, current_user)

    ai_action = AIActionService.create_action_record(
        session=session,
        user=current_user,
        transcription_id=action_request.transcription_id,
        action_type="voice/fix-grammar",
        request_params=action_request.options,
        quota_cost=1
    )

    # Execute AI action
    ai_action = await AIActionService.execute_ai_action(
        session=session,
        ai_action=ai_action,
        transcription=transcription,
        user=current_user
    )

    quota_remaining = current_user.ai_action_quota_daily - current_user.ai_action_count_today

    return AIActionResponse(
        action_id=ai_action.action_id,
        status=ai_action.status,
        message=json.loads(ai_action.result_data).get("text") if ai_action.result_data else None,
        quota_remaining=quota_remaining,
        quota_reset_date=str(current_user.quota_reset_date),
        result=json.loads(ai_action.result_data) if ai_action.result_data else None,
        error=ai_action.error_message,
        created_at=ai_action.created_at,
        completed_at=ai_action.completed_at,
        session_id=json.loads(ai_action.result_data).get("session_id") if ai_action.result_data else None
    )


@router.post("/voice/convert-spoken-to-written", response_model=AIActionResponse, status_code=status.HTTP_200_OK)
@require_quota(cost=1)
@track_usage(action_type="voice/convert-spoken-to-written")
async def convert_spoken_to_written(
    action_request: AIActionRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Convert spoken language style to written prose.

    **Quota Cost:** 1 action

    **Request Parameters:**
    - `transcription_id`: ID of the transcription to process
    - `options.formality`: Formality level ("casual", "medium", "formal")

    **Returns:**
    - Actual AI-generated written prose with quota information
    """
    transcription = AIActionService.verify_transcription_access(session, action_request.transcription_id, current_user)

    ai_action = AIActionService.create_action_record(
        session=session,
        user=current_user,
        transcription_id=action_request.transcription_id,
        action_type="voice/convert-spoken-to-written",
        request_params=action_request.options,
        quota_cost=1
    )

    # Execute AI action
    ai_action = await AIActionService.execute_ai_action(
        session=session,
        ai_action=ai_action,
        transcription=transcription,
        user=current_user
    )

    quota_remaining = current_user.ai_action_quota_daily - current_user.ai_action_count_today

    return AIActionResponse(
        action_id=ai_action.action_id,
        status=ai_action.status,
        message=json.loads(ai_action.result_data).get("text") if ai_action.result_data else None,
        quota_remaining=quota_remaining,
        quota_reset_date=str(current_user.quota_reset_date),
        result=json.loads(ai_action.result_data) if ai_action.result_data else None,
        error=ai_action.error_message,
        created_at=ai_action.created_at,
        completed_at=ai_action.completed_at,
        session_id=json.loads(ai_action.result_data).get("session_id") if ai_action.result_data else None
    )


# ============================================================================
# Category 6: Multi-turn Conversation (Session-based)
# ============================================================================

@router.post("/improve/{action_id}", response_model=AIActionResponse, status_code=status.HTTP_200_OK)
@require_quota(cost=1)
@track_usage(action_type="improve")
async def improve_action(
    action_id: str,
    improve_request: ImproveActionRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Improve a previous AI action result with additional instructions.

    **Quota Cost:** 1 action

    **Request Parameters:**
    - `session_id`: The session ID from the original action (required)
    - `instructions`: How to improve the result (e.g., "make it shorter and more professional")

    **Returns:**
    - Improved AI-generated result with quota information
    - Same session_id for continued conversation

    **Example:**
    ```json
    {
      "session_id": "abc-123-def",
      "instructions": "Make it more concise and add bullet points"
    }
    ```

    **Use Case:**
    User receives an AI-generated result, then refines it with follow-up instructions
    without losing conversation context.
    """
    logger.info(
        f"Improve action requested: action_id={action_id}, user_id={current_user.id}, "
        f"session_id={improve_request.session_id}, instructions={improve_request.instructions[:50]}..."
    )

    # Verify the original action exists and belongs to the user
    original_action = AIActionService.get_action_by_id(session, action_id, current_user)

    if not original_action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI action {action_id} not found"
        )

    # Get the transcription for context
    transcription = AIActionService.verify_transcription_access(
        session,
        original_action.transcription_id,
        current_user
    )

    # Create new AI action record for the improvement
    ai_action = AIActionService.create_action_record(
        session=session,
        user=current_user,
        transcription_id=original_action.transcription_id,
        action_type="improve",
        request_params={"original_action_id": action_id, "instructions": improve_request.instructions},
        quota_cost=1
    )

    try:
        # Get prompts for improvement
        system_prompt, user_prompt = get_improve_prompts(improve_request.instructions)

        # Create LlamaAgent service with session reuse
        agent_service = LlamaAgentService(
            user_id=current_user.id,
            transcription_id=transcription.id,
            action_type="improve",
            session_id=improve_request.session_id  # Reuse existing session
        )

        logger.info(
            f"Executing improve action with session reuse: session_id={improve_request.session_id}, "
            f"action_id={ai_action.action_id}"
        )

        # Execute improvement (returns tuple: result_text, session_id)
        result_text, returned_session_id = await agent_service.run(system_prompt, user_prompt)

        # Update AI action record
        ai_action.status = "completed"
        ai_action.result_data = json.dumps({
            "text": result_text,
            "session_id": returned_session_id,
            "original_action_id": action_id
        })
        ai_action.completed_at = datetime.utcnow()
        ai_action.error_message = None

        session.add(ai_action)
        session.commit()
        session.refresh(ai_action)

        logger.info(
            f"Improve action completed: action_id={ai_action.action_id}, "
            f"session_id={returned_session_id}, result_length={len(result_text)}"
        )

    except Exception as e:
        logger.error(
            f"Improve action failed: action_id={ai_action.action_id}, error={str(e)}"
        )
        ai_action.status = "failed"
        ai_action.error_message = str(e)
        ai_action.completed_at = datetime.utcnow()
        session.add(ai_action)
        session.commit()
        session.refresh(ai_action)

    quota_remaining = current_user.ai_action_quota_daily - current_user.ai_action_count_today

    return AIActionResponse(
        action_id=ai_action.action_id,
        status=ai_action.status,
        message=json.loads(ai_action.result_data).get("text") if ai_action.result_data else None,
        quota_remaining=quota_remaining,
        quota_reset_date=str(current_user.quota_reset_date),
        result=json.loads(ai_action.result_data) if ai_action.result_data else None,
        error=ai_action.error_message,
        created_at=ai_action.created_at,
        completed_at=ai_action.completed_at,
        session_id=json.loads(ai_action.result_data).get("session_id") if ai_action.result_data else None
    )


@router.post("/chat", response_model=AIActionResponse, status_code=status.HTTP_200_OK)
@require_quota(cost=1)
@track_usage(action_type="chat")
async def chat_with_model(
    chat_request: ChatRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Chat with the AI model for testing or general assistance.

    **Quota Cost:** 1 action

    **Request Parameters:**
    - `message`: Your message to the AI (required)
    - `session_id`: Optional - continue existing conversation
    - `transcription_id`: Optional - chat about a specific transcription

    **Returns:**
    - AI response with quota information
    - session_id for continuing the conversation

    **Example - New Chat:**
    ```json
    {
      "message": "Hello, can you help me write a professional email?"
    }
    ```

    **Example - Continue Chat:**
    ```json
    {
      "message": "Make it more formal",
      "session_id": "abc-123-def"
    }
    ```

    **Example - Chat about Transcription:**
    ```json
    {
      "message": "Summarize the key points",
      "transcription_id": 123
    }
    ```

    **Use Cases:**
    - Test LlamaStack configuration
    - Get AI assistance with writing tasks
    - Multi-turn conversations about transcriptions
    - Exploratory dialog with the AI model
    """
    logger.info(
        f"Chat requested: user_id={current_user.id}, message={chat_request.message[:50]}..., "
        f"session_id={chat_request.session_id}, transcription_id={chat_request.transcription_id}"
    )

    # Get transcription text if provided
    transcription_text = None
    transcription_id_for_record = chat_request.transcription_id  # None if no transcription provided

    if chat_request.transcription_id:
        transcription = AIActionService.verify_transcription_access(
            session,
            chat_request.transcription_id,
            current_user
        )
        transcription_text = transcription.text

    # Create AI action record
    ai_action = AIActionService.create_action_record(
        session=session,
        user=current_user,
        transcription_id=transcription_id_for_record,
        action_type="chat",
        request_params={
            "message": chat_request.message,
            "has_transcription": chat_request.transcription_id is not None,
            "session_id": chat_request.session_id
        },
        quota_cost=1
    )

    try:
        # Get chat prompts
        system_prompt, user_prompt = get_chat_prompts(
            chat_request.message,
            transcription_text
        )

        # Create LlamaAgent service (may reuse session if provided)
        agent_service = LlamaAgentService(
            user_id=current_user.id,
            transcription_id=transcription_id_for_record,
            action_type="chat",
            session_id=chat_request.session_id  # May be None for new chat
        )

        if chat_request.session_id:
            logger.info(
                f"Continuing chat session: session_id={chat_request.session_id}, "
                f"action_id={ai_action.action_id}"
            )
        else:
            logger.info(f"Starting new chat session: action_id={ai_action.action_id}")

        # Execute chat (returns tuple: result_text, session_id)
        result_text, returned_session_id = await agent_service.run(system_prompt, user_prompt)

        # Update AI action record
        ai_action.status = "completed"
        ai_action.result_data = json.dumps({
            "text": result_text,
            "session_id": returned_session_id
        })
        ai_action.completed_at = datetime.utcnow()
        ai_action.error_message = None

        session.add(ai_action)
        session.commit()
        session.refresh(ai_action)

        logger.info(
            f"Chat completed: action_id={ai_action.action_id}, "
            f"session_id={returned_session_id}, result_length={len(result_text)}"
        )

    except Exception as e:
        logger.error(f"Chat failed: action_id={ai_action.action_id}, error={str(e)}")
        ai_action.status = "failed"
        ai_action.error_message = str(e)
        ai_action.completed_at = datetime.utcnow()
        session.add(ai_action)
        session.commit()
        session.refresh(ai_action)

    quota_remaining = current_user.ai_action_quota_daily - current_user.ai_action_count_today

    return AIActionResponse(
        action_id=ai_action.action_id,
        status=ai_action.status,
        message=json.loads(ai_action.result_data).get("text") if ai_action.result_data else None,
        quota_remaining=quota_remaining,
        quota_reset_date=str(current_user.quota_reset_date),
        result=json.loads(ai_action.result_data) if ai_action.result_data else None,
        error=ai_action.error_message,
        created_at=ai_action.created_at,
        completed_at=ai_action.completed_at,
        session_id=json.loads(ai_action.result_data).get("session_id") if ai_action.result_data else None
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cleanup_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Cleanup a LlamaStack session when no longer needed.

    This endpoint should be called when:
    - User closes the AI action modal
    - User navigates away from the page
    - Session is no longer needed

    **Note:** Sessions also auto-cleanup after 30 minutes of inactivity (future implementation).

    **Parameters:**
    - `session_id`: The LlamaStack session ID to cleanup

    **Returns:**
    - 204 No Content on success
    - 401 Unauthorized if not authenticated

    **Example:**
    ```bash
    curl -X DELETE "http://localhost:8000/api/v1/actions/sessions/abc-123-def" \
      -H "Authorization: Bearer $TOKEN"
    ```

    **Best Practice:**
    Always cleanup sessions when done to prevent memory leaks on the LlamaStack server.
    """
    logger.info(
        f"Session cleanup requested: session_id={session_id}, user_id={current_user.id}"
    )

    try:
        # Create a temporary agent service just for cleanup
        # We use dummy values for user_id, transcription_id, and action_type since we're just cleaning up
        agent_service = LlamaAgentService(
            user_id=current_user.id,
            transcription_id=0,  # Not relevant for cleanup
            action_type="cleanup"
        )

        # Cleanup the session (best-effort, errors are logged but don't fail the request)
        await agent_service.cleanup_session(session_id)

        logger.info(
            f"Session cleanup completed: session_id={session_id}, user_id={current_user.id}"
        )

        security_logger.info(
            f"Session cleanup: session_id={session_id}, user_id={current_user.id}, explicit=True"
        )

    except Exception as e:
        # Log error but still return 204 (cleanup is best-effort)
        logger.warning(
            f"Session cleanup failed (non-critical): session_id={session_id}, "
            f"user_id={current_user.id}, error={str(e)}"
        )

    # Always return 204 No Content (idempotent operation)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
