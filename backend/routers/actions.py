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
from backend.models import User, AIActionRequest, AIActionResponse
from backend.services.ai_action_service import AIActionService
from backend.services.permission_service import PermissionService
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
        completed_at=ai_action.completed_at
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
        completed_at=ai_action.completed_at
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
        completed_at=ai_action.completed_at
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
        completed_at=ai_action.completed_at
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
        completed_at=ai_action.completed_at
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
        completed_at=ai_action.completed_at
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
        completed_at=ai_action.completed_at
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
        completed_at=ai_action.completed_at
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
        completed_at=ai_action.completed_at
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
        completed_at=ai_action.completed_at
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
        completed_at=ai_action.completed_at
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
        completed_at=ai_action.completed_at
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
        completed_at=ai_action.completed_at
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
        completed_at=ai_action.completed_at
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
        completed_at=ai_action.completed_at
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
        completed_at=ai_action.completed_at
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
        completed_at=ai_action.completed_at
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
        completed_at=ai_action.completed_at
    )
