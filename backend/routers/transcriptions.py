"""
Transcription API Router

This module defines all API endpoints related to transcription operations.
Following the thin controller pattern, endpoints delegate business logic
to the service layer.

Endpoints:
- POST /api/transcribe - Upload and transcribe audio
- GET /api/transcriptions - List user's transcriptions (paginated)
- GET /api/transcriptions/{id} - Get specific transcription
- GET /api/transcriptions/{id}/status - Get transcription status
- GET /api/transcriptions/status/bulk - Get multiple transcription statuses
- GET /api/transcriptions/{id}/audio - Stream audio file
- GET /api/transcriptions/{id}/download - Download ZIP package
- PATCH /api/transcriptions/{id} - Update transcription (priority)
- DELETE /api/transcriptions/{id} - Delete transcription
"""

import logging
from typing import Annotated, Optional

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import Response, StreamingResponse
from sqlmodel import Session

from backend.auth import get_current_active_user, get_user_from_query_token
from backend.config import settings
from backend.database import get_session
from backend.models import (
    BulkStatusResponse,
    Transcription,
    TranscriptionList,
    TranscriptionPublic,
    TranscriptionStatusResponse,
    TranscriptionUpdate,
    User,
)
from backend.services.transcription_service import TranscriptionService
from backend.middleware.rate_limiter import transcription_rate_limit

# Configure logger
logger = logging.getLogger(__name__)

# Create router with common prefix and tags
router = APIRouter(
    prefix="/api",
    tags=["transcriptions"],
    responses={404: {"description": "Not found"}},
)


@router.post("/transcribe", response_model=TranscriptionPublic)
@transcription_rate_limit()
async def transcribe_audio(
    request: Request,
    response: Response,
    file: Annotated[UploadFile, File(description="Audio file to transcribe")],
    url: Annotated[str | None, Form(description="Optional URL associated with the voice note")] = None,
    model: Annotated[str | None, Form(description="Model to use for transcription")] = None,
    enable_diarization: Annotated[bool, Form(description="Enable speaker diarization")] = False,
    num_speakers: Annotated[int | None, Form(description="Number of speakers (optional)")] = None,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """
    Upload audio file and dispatch background transcription task.

    **Rate Limit**: 10 requests per minute per user

    This endpoint works asynchronously:
    1. Validates and saves audio file to database
    2. Dispatches Celery task for transcription
    3. Returns immediately with status="pending"
    4. Client polls /api/transcriptions/{id}/status for updates

    Authentication: Requires valid JWT token.
    Transcription will be associated with the authenticated user.

    Args:
        file: Audio file uploaded via multipart/form-data
        url: Optional URL associated with the voice note
        model: Model name to use for transcription (defaults to DEFAULT_MODEL)
        enable_diarization: Enable speaker diarization (default: False)
        num_speakers: Number of speakers to detect (optional, auto-detect if not specified)
        current_user: Authenticated user (injected)
        session: Database session (injected)

    Returns:
        TranscriptionPublic: Created transcription with status="pending"

    Raises:
        HTTPException 400: Invalid file type, model, or audio too long
        HTTPException 413: File too large
        HTTPException 500: Processing or task dispatch failure
    """
    try:
        # Determine which model to use
        selected_model = model if model else settings.DEFAULT_MODEL

        # Process audio upload (validation, conversion, duration extraction)
        audio_bytes, content_type, filename, duration = await TranscriptionService.process_audio_upload(
            file, selected_model
        )

        logger.info(f"Model: {selected_model}, Diarization: {enable_diarization}")

        # Create database record with status="pending"
        db_transcription = TranscriptionService.create_transcription_record(
            session=session,
            audio_bytes=audio_bytes,
            audio_filename=filename,
            audio_content_type=content_type,
            duration_seconds=duration,
            url=url,
            user=current_user
        )

        # Dispatch Celery task for background processing
        task_id = TranscriptionService.dispatch_transcription_task(
            transcription_id=db_transcription.id,
            model=selected_model,
            enable_diarization=enable_diarization,
            num_speakers=num_speakers,
            session=session
        )

        # Return transcription with status="pending"
        return TranscriptionService.to_public_schema(db_transcription)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Critical error during audio upload: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process audio upload: {str(e)}"
        )


@router.get("/transcriptions", response_model=TranscriptionList)
def list_transcriptions(
    skip: int = 0,
    limit: int | None = None,
    priority: str | None = None,
    search: str | None = None,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """
    List user's transcriptions with pagination, optional priority filtering, and search.

    Authentication: Requires valid JWT token.
    Only returns transcriptions belonging to the authenticated user.

    Args:
        skip: Number of records to skip (offset for pagination)
        limit: Maximum number of records to return (defaults to DEFAULT_PAGE_SIZE, max: MAX_PAGE_SIZE)
        priority: Optional priority filter (low, medium, high)
        search: Optional search query (searches in transcription text, case-insensitive)
        current_user: Authenticated user (injected)
        session: Database session (injected)

    Returns:
        TranscriptionList: Paginated list of user's transcriptions with total count
    """
    # Get transcriptions from service layer
    transcriptions, total = TranscriptionService.get_user_transcriptions(
        session=session,
        user=current_user,
        skip=skip,
        limit=limit,
        priority=priority,
        search=search
    )

    # Convert to public schema
    public_transcriptions = [
        TranscriptionService.to_public_schema(t) for t in transcriptions
    ]

    # Use actual limit (after applying defaults and max)
    actual_limit = limit if limit else settings.DEFAULT_PAGE_SIZE
    actual_limit = min(actual_limit, settings.MAX_PAGE_SIZE)

    return TranscriptionList(
        transcriptions=public_transcriptions,
        total=total,
        skip=skip,
        limit=actual_limit,
    )


@router.get("/transcriptions/{transcription_id}/status", response_model=TranscriptionStatusResponse)
def get_transcription_status(
    transcription_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """
    Get the current status of a transcription task.

    This endpoint is used by the frontend to poll for transcription progress.
    Returns current status, progress percentage, and any error messages.

    Authentication: Requires valid JWT token.
    Only allows access if transcription belongs to authenticated user.

    Args:
        transcription_id: ID of the transcription
        current_user: Authenticated user (injected)
        session: Database session (injected)

    Returns:
        TranscriptionStatusResponse: Status information

    Raises:
        HTTPException 404: Transcription not found
        HTTPException 403: Not authorized to view this transcription
    """
    # Get transcription (verifies ownership)
    transcription = TranscriptionService.get_transcription_by_id(
        session, transcription_id, current_user
    )

    # If task is still pending or processing, check Celery task status
    if transcription.task_id and transcription.status in ["pending", "processing"]:
        try:
            task_result = AsyncResult(transcription.task_id)
            celery_state = task_result.state

            # Update status based on Celery state
            if celery_state == "PENDING":
                # Task not started yet
                pass  # Keep database status
            elif celery_state == "PROCESSING":
                # Task is running, get progress from meta
                meta = task_result.info or {}
                if isinstance(meta, dict):
                    transcription.progress = meta.get('progress', transcription.progress)
            elif celery_state == "SUCCESS":
                # Task completed, should be updated in database already
                pass
            elif celery_state == "FAILURE":
                # Task failed
                if transcription.status != "failed":
                    transcription.status = "failed"
                    transcription.error_message = str(task_result.info)
                    session.commit()

        except Exception as e:
            logger.error(f"Error checking Celery task status: {e}")

    return TranscriptionStatusResponse(
        id=transcription.id,
        status=transcription.status,
        progress=transcription.progress,
        task_id=transcription.task_id,
        error_message=transcription.error_message
    )


@router.get("/transcriptions/status/bulk", response_model=BulkStatusResponse)
def get_bulk_transcription_status(
    ids: str,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """
    Get status for multiple transcriptions at once.

    This endpoint allows efficient polling of multiple transcriptions.
    Useful for updating the transcription list view.

    Authentication: Requires valid JWT token.
    Only returns status for transcriptions belonging to authenticated user.

    Args:
        ids: Comma-separated list of transcription IDs (e.g., "1,2,3")
        current_user: Authenticated user (injected)
        session: Database session (injected)

    Returns:
        BulkStatusResponse: List of status objects for requested transcriptions

    Raises:
        HTTPException 400: Invalid ID format or too many IDs (max 50)
    """
    # Parse IDs
    try:
        id_list = [int(id_str.strip()) for id_str in ids.split(',') if id_str.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    # Limit to 50 IDs
    if len(id_list) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 IDs allowed")

    # Get transcriptions (only those belonging to user)
    transcriptions = session.query(Transcription).filter(
        Transcription.id.in_(id_list),
        Transcription.user_id == current_user.id
    ).all()

    # Build status list
    statuses = [
        TranscriptionStatusResponse(
            id=t.id,
            status=t.status,
            progress=t.progress,
            task_id=t.task_id,
            error_message=t.error_message
        )
        for t in transcriptions
    ]

    return BulkStatusResponse(statuses=statuses)


@router.get("/transcriptions/{transcription_id}", response_model=TranscriptionPublic)
def get_transcription(
    transcription_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """
    Get a specific transcription by ID.

    Authentication: Requires valid JWT token.
    Only returns transcription if it belongs to the authenticated user.

    Args:
        transcription_id: ID of the transcription
        current_user: Authenticated user (injected)
        session: Database session (injected)

    Returns:
        TranscriptionPublic: Transcription details (without binary audio data)

    Raises:
        HTTPException 404: Transcription not found
        HTTPException 403: Not authorized to access this transcription
    """
    transcription = TranscriptionService.get_transcription_by_id(
        session, transcription_id, current_user
    )

    return TranscriptionService.to_public_schema(transcription)


@router.get("/transcriptions/{transcription_id}/audio")
async def get_audio(
    transcription_id: int,
    format: Optional[str] = Query(None, description="Target audio format (wav, mp3, ogg, webm). If not specified, returns original format."),
    current_user: User = Depends(get_user_from_query_token),
    session: Session = Depends(get_session)
):
    """
    Stream the audio file for a specific transcription from MinIO storage.

    This endpoint uses query parameter authentication to support HTML audio elements
    that cannot set Authorization headers.

    Supports on-demand format conversion via the ?format= query parameter.
    Conversion happens on celery worker (not backend) to keep backend lightweight.
    Converted files are NOT cached to save storage space.

    Authentication: Requires token as query parameter (?token=xxx).
    Only allows access if transcription belongs to the authenticated user.

    Args:
        transcription_id: ID of the transcription
        format: Optional target audio format (wav, mp3, ogg, webm). Defaults to original format.
        current_user: Authenticated user from query token (injected)
        session: Database session (injected)

    Returns:
        Response: Audio file as binary data with appropriate MIME type

    Raises:
        HTTPException 401: Token missing or invalid
        HTTPException 404: Transcription not found
        HTTPException 403: Not authorized to access this transcription
        HTTPException 500: Format conversion failed

    Examples:
        <audio src="/api/transcriptions/123/audio?token=YOUR_JWT_TOKEN" />
        <audio src="/api/transcriptions/123/audio?token=YOUR_JWT_TOKEN&format=wav" />
    """
    from backend.services.minio_service import get_minio_service
    from backend.celery_app import celery_app

    transcription = TranscriptionService.get_transcription_by_id(
        session, transcription_id, current_user
    )

    # Determine if format conversion is needed
    source_content_type = transcription.audio_content_type or "audio/webm"
    format_mapping = {
        'audio/webm': 'webm',
        'audio/wav': 'wav',
        'audio/wave': 'wav',
        'audio/x-wav': 'wav',
        'audio/mpeg': 'mp3',
        'audio/mp3': 'mp3',
        'audio/ogg': 'ogg',
    }
    source_format = format_mapping.get(source_content_type, 'webm')

    # If format conversion requested and different from source
    if format and format.lower() != source_format:
        logger.info(f"Format conversion requested: {source_format} -> {format}")

        # Dispatch synchronous celery task to worker for conversion
        # Worker has all audio processing dependencies (pydub, ffmpeg)
        try:
            task_result = celery_app.send_task(
                'backend.tasks.convert_audio_format',
                kwargs={
                    'transcription_id': transcription_id,
                    'target_format': format.lower()
                }
            )

            # Wait for conversion to complete (timeout 60s)
            audio_data = task_result.get(timeout=60)

            # Map format to MIME type
            mime_mapping = {
                'wav': 'audio/wav',
                'mp3': 'audio/mpeg',
                'ogg': 'audio/ogg',
                'webm': 'audio/webm',
            }
            content_type = mime_mapping.get(format.lower(), 'audio/wav')

            # Update filename extension
            import os
            base_name = os.path.splitext(transcription.audio_filename)[0]
            filename = f"{base_name}.{format.lower()}"

        except Exception as e:
            logger.error(f"Format conversion failed: {e}")
            raise HTTPException(status_code=500, detail=f"Format conversion failed: {str(e)}")
    else:
        # No conversion needed, return original
        # Get audio from MinIO or fallback to legacy database BLOB
        if transcription.minio_object_path:
            # New: Fetch from MinIO
            try:
                minio_service = get_minio_service()
                audio_data = minio_service.download_audio(transcription.minio_object_path)
            except Exception as e:
                logger.error(f"Failed to download audio from MinIO: {e}")
                raise HTTPException(status_code=500, detail="Failed to retrieve audio file")
        elif transcription.audio_data:
            # Legacy: Fetch from database BLOB
            audio_data = transcription.audio_data
        else:
            raise HTTPException(status_code=404, detail="Audio file not found")

        content_type = transcription.audio_content_type
        filename = transcription.audio_filename

    return Response(
        content=audio_data,
        media_type=content_type,
        headers={
            "Content-Disposition": f'inline; filename="{filename}"'
        }
    )


@router.get("/transcriptions/{transcription_id}/download")
async def download_transcription(
    transcription_id: int,
    format: Optional[str] = Query(None, description="Audio format (webm, wav, mp3). Defaults to wav."),
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """
    Download a transcription as a ZIP file containing:
    - {username}.{format}: Audio file in specified format (default: wav)
    - config.json: Transcription metadata and text

    Authentication: Requires valid JWT token.
    Only allows download if transcription belongs to the authenticated user.

    Args:
        transcription_id: ID of the transcription
        format: Audio format (webm, wav, mp3). Defaults to wav if not specified.
        current_user: Authenticated user (injected)
        session: Database session (injected)

    Returns:
        StreamingResponse: ZIP file containing audio and config

    Raises:
        HTTPException 404: Transcription not found
        HTTPException 403: Not authorized to access this transcription
        HTTPException 500: ZIP creation or audio conversion failed
    """
    transcription = TranscriptionService.get_transcription_by_id(
        session, transcription_id, current_user
    )

    # Default to wav if no format specified
    target_format = format.lower() if format else 'wav'

    # Create ZIP package with specified format
    zip_buffer = TranscriptionService.create_download_package(
        transcription, current_user.username, target_format
    )

    # Generate a meaningful filename for the ZIP
    zip_filename = f"transcription_{transcription_id}_{current_user.username}.zip"

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{zip_filename}"'
        }
    )


@router.patch("/transcriptions/{transcription_id}", response_model=TranscriptionPublic)
def update_transcription_priority(
    transcription_id: int,
    priority: str,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """
    Update the priority of a transcription.

    Authentication: Requires valid JWT token.
    Only allows update if transcription belongs to the authenticated user.

    Args:
        transcription_id: ID of the transcription to update
        priority: New priority value (low, medium, high)
        current_user: Authenticated user (injected)
        session: Database session (injected)

    Returns:
        TranscriptionPublic: Updated transcription

    Raises:
        HTTPException 400: Invalid priority value
        HTTPException 404: Transcription not found
        HTTPException 403: Not authorized to update this transcription
    """
    transcription = TranscriptionService.update_transcription_priority(
        session, transcription_id, priority, current_user
    )

    return TranscriptionService.to_public_schema(transcription)


@router.delete("/transcriptions/{transcription_id}")
def delete_transcription(
    transcription_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """
    Delete a transcription and its audio file.

    Authentication: Requires valid JWT token.
    Only allows deletion if transcription belongs to the authenticated user.

    Args:
        transcription_id: ID of the transcription to delete
        current_user: Authenticated user (injected)
        session: Database session (injected)

    Returns:
        dict: Success message

    Raises:
        HTTPException 404: Transcription not found
        HTTPException 403: Not authorized to delete this transcription
    """
    TranscriptionService.delete_transcription(session, transcription_id, current_user)

    return {"message": "Transcription deleted successfully"}


@router.post("/transcriptions/{transcription_id}/re-transcribe", response_model=TranscriptionPublic)
def re_transcribe(
    transcription_id: int,
    model: Annotated[str | None, Form(description="Model to use for transcription")] = None,
    url: Annotated[str | None, Form(description="Optional URL associated with the voice note")] = None,
    enable_diarization: Annotated[bool, Form(description="Enable speaker diarization")] = False,
    num_speakers: Annotated[int | None, Form(description="Number of speakers (optional)")] = None,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """
    Re-transcribe an existing transcription with new options.

    This endpoint allows re-processing an existing audio file with different:
    - Transcription model
    - Diarization settings
    - Number of speakers
    - Associated URL

    Authentication: Requires valid JWT token.
    Only allows re-transcription if original transcription belongs to the authenticated user.

    Args:
        transcription_id: ID of the transcription to re-transcribe
        model: Model name to use for transcription (defaults to DEFAULT_MODEL)
        url: Optional URL to associate with the re-transcription
        enable_diarization: Enable speaker diarization (default: False)
        num_speakers: Number of speakers to detect (optional, auto-detect if not specified)
        current_user: Authenticated user (injected)
        session: Database session (injected)

    Returns:
        TranscriptionPublic: Updated transcription with status="pending"

    Raises:
        HTTPException 404: Transcription not found
        HTTPException 403: Not authorized to re-transcribe this transcription
        HTTPException 500: Re-transcription task dispatch failure
    """
    try:
        # Get the existing transcription (verifies ownership)
        original = TranscriptionService.get_transcription_by_id(
            session, transcription_id, current_user
        )

        # Determine which model to use
        selected_model = model if model else settings.DEFAULT_MODEL

        logger.info(f"Re-transcribing transcription {transcription_id} with model: {selected_model}, diarization: {enable_diarization}")

        # Update transcription status to pending and clear previous results
        original.status = "pending"
        original.progress = 0
        original.text = ""
        original.error_message = None
        original.task_id = None

        # Update URL if provided
        if url is not None:
            original.url = url

        session.commit()
        session.refresh(original)

        # Dispatch Celery task for background processing with new options
        task_id = TranscriptionService.dispatch_transcription_task(
            transcription_id=original.id,
            model=selected_model,
            enable_diarization=enable_diarization,
            num_speakers=num_speakers,
            session=session
        )

        # Return transcription with status="pending"
        return TranscriptionService.to_public_schema(original)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Critical error during re-transcription: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to re-transcribe: {str(e)}"
        )


@router.delete("/transcriptions/{transcription_id}/audio", response_model=TranscriptionPublic)
def delete_audio_file(
    transcription_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """
    Delete the audio file from storage while keeping the transcription text.

    This endpoint removes the audio file from MinIO storage and updates the
    transcription record to reflect that the audio is no longer available.
    The transcription text remains intact.

    Args:
        transcription_id: ID of the transcription whose audio should be deleted
        current_user: Currently authenticated user
        session: Database session

    Returns:
        TranscriptionPublic: Updated transcription without audio file

    Raises:
        HTTPException: If transcription not found or user lacks permission
    """
    try:
        # Get the transcription (verifies ownership)
        transcription = TranscriptionService.get_transcription_by_id(
            session, transcription_id, current_user
        )

        # Delete audio file from MinIO if it exists
        if transcription.audio_filename:
            try:
                TranscriptionService.delete_audio_from_storage(
                    user_id=current_user.id,
                    transcription_id=transcription.id,
                    filename=transcription.audio_filename
                )
                logger.info(f"Deleted audio file for transcription {transcription_id}")
            except Exception as e:
                logger.warning(f"Failed to delete audio file from storage: {e}")
                # Continue anyway to update the database record

        # Update transcription to reflect audio deletion
        transcription.audio_filename = None
        transcription.duration_seconds = None

        session.commit()
        session.refresh(transcription)

        return TranscriptionService.to_public_schema(transcription)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete audio file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete audio file: {str(e)}"
        )


@router.get("/models")
def get_models():
    """
    Get list of available transcription models.

    No authentication required.

    Returns:
        dict: Available models and default model configuration
    """
    return {
        "models": list(settings.MODELS.keys()),
        "default": settings.DEFAULT_MODEL
    }
