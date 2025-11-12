"""
EchoNote FastAPI Backend

A modern voice transcription API that stores audio recordings and their
transcriptions using Whisper (via vLLM) and SQLModel.
"""

# Configure matplotlib before any imports (defensive measure for diarization)
# This is also set in diarization.py, but setting it here ensures it's
# configured even if matplotlib gets imported indirectly
import os
os.environ['MPLBACKEND'] = 'Agg'
os.environ['MPLCONFIGDIR'] = '/tmp/matplotlib'

import json
import logging
import zipfile
from io import BytesIO
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from openai import AsyncOpenAI
from sqlmodel import Session, select

from backend.auth import get_current_active_user
from backend.auth_routes import router as auth_router
from backend.config import settings
from backend.database import create_db_and_tables, get_session
from backend.diarization import get_diarization_service
from backend.models import Priority, Transcription, TranscriptionList, TranscriptionPublic, User

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="EchoNote API",
    description="Voice transcription API with audio storage",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication routes
app.include_router(auth_router)

# OpenAI clients will be created dynamically per request based on selected model
logger.info(f"Available transcription models: {list(settings.MODELS.keys())}")
logger.info(f"Default transcription model: {settings.DEFAULT_MODEL}")

# Log AI assistant models if configured
if settings.ASSISTANT_MODELS:
    logger.info(f"Available AI assistant models: {list(settings.ASSISTANT_MODELS.keys())}")
    logger.info(f"Default AI assistant model: {settings.DEFAULT_ASSISTANT_MODEL}")
else:
    logger.info("No AI assistant models configured")


def extract_transcription_text(response) -> str:
    """
    Extract transcription text from various response formats.

    Handles different formats returned by OpenAI-compatible Whisper endpoints:
    - Direct string responses
    - JSON strings containing text
    - Objects with .text attribute
    - Dicts with 'text' key
    - Dicts with 'choices' array (chat-completion style)

    Args:
        response: The response from the transcription API

    Returns:
        str: The extracted transcription text
    """
    # If it's a string, check if it's JSON
    if isinstance(response, str):
        # Try to parse as JSON
        try:
            parsed = json.loads(response)
            if isinstance(parsed, dict) and "text" in parsed:
                return parsed["text"]
        except (json.JSONDecodeError, TypeError):
            # Not JSON, return as-is
            pass
        return response

    # Check for .text attribute (OpenAI style)
    text = getattr(response, "text", None)
    if text is not None:
        return text

    # Handle dict responses
    if isinstance(response, dict):
        # Direct text key
        if "text" in response:
            return response["text"]

        # Chat completion style with choices
        if "choices" in response and response["choices"]:
            choice = response["choices"][0]
            if isinstance(choice, dict) and "text" in choice:
                return choice["text"]

    # Fallback: convert to string and log warning
    logger.warning(f"Unexpected response format: {type(response)}, converting to string")
    return str(response)




@app.on_event("startup")
def on_startup():
    """Initialize database on application startup."""
    logger.info("Creating database tables...")
    create_db_and_tables()
    logger.info("Database initialized successfully")


@app.get("/")
def read_root():
    """Health check endpoint."""
    return {
        "app": "EchoNote API",
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/api/models")
def get_models():
    """
    Get list of available transcription models.

    Returns:
        dict: Available models and default model
    """
    return {
        "models": list(settings.MODELS.keys()),
        "default": settings.DEFAULT_MODEL
    }


@app.post("/api/transcribe", response_model=TranscriptionPublic)
async def transcribe_audio(
    file: Annotated[UploadFile, File(description="Audio file to transcribe")],
    url: Annotated[str | None, Form(description="Optional URL associated with the voice note")] = None,
    model: Annotated[str | None, Form(description="Model to use for transcription")] = None,
    enable_diarization: Annotated[bool, Form(description="Enable speaker diarization")] = False,
    num_speakers: Annotated[int | None, Form(description="Number of speakers (optional)")] = None,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """
    Transcribe an audio file and store it in the database.

    Requires authentication. Transcription will be associated with the authenticated user.

    Args:
        file: Audio file uploaded via multipart/form-data
        url: Optional URL associated with the voice note
        model: Model name to use for transcription (defaults to DEFAULT_MODEL)
        enable_diarization: Enable speaker diarization (default: False)
        num_speakers: Number of speakers to detect (optional, auto-detect if not specified)
        session: Database session dependency

    Returns:
        TranscriptionPublic: Created transcription without binary data
    """
    # Determine which model to use
    selected_model = model if model else settings.DEFAULT_MODEL

    # Validate model exists
    if selected_model not in settings.MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model: {selected_model}. Available models: {list(settings.MODELS.keys())}"
        )
    # Validate file type
    if file.content_type not in settings.ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid audio type. Allowed types: {settings.ALLOWED_AUDIO_TYPES}"
        )

    try:
        # Read audio file
        audio_bytes = await file.read()

        # Check file size
        if len(audio_bytes) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE} bytes"
            )

        logger.info(f"Processing audio file: {file.filename} ({len(audio_bytes)} bytes)")
        logger.info(f"Content type: {file.content_type}")
        logger.info(f"Using model: {selected_model}")
        logger.info(f"Diarization enabled: {enable_diarization}")

        # Get the base URL for the selected model
        model_base_url = settings.get_model_url(selected_model)

        # Create OpenAI client for this specific model
        client = AsyncOpenAI(
            base_url=model_base_url,
            api_key=settings.API_KEY,
        )

        # Track actual content type (will be updated if we convert)
        actual_content_type = file.content_type
        actual_filename = file.filename

        # Convert WebM to WAV if needed (vLLM Whisper has issues with WebM)
        # WebM conversion runs in isolated subprocess to prevent memory conflicts
        if file.content_type == "audio/webm":
            try:
                from backend.audio_converter import convert_webm_to_wav
                import gc
                import sys

                # Convert in isolated subprocess (see audio_converter.py)
                wav_bytes = convert_webm_to_wav(audio_bytes)

                # Clean up converter module from memory
                modules_to_remove = [m for m in sys.modules.keys() if 'pydub' in m.lower()]
                for module_name in modules_to_remove:
                    del sys.modules[module_name]
                del convert_webm_to_wav

                # Force garbage collection to free memory
                gc.collect()
                gc.collect()
                gc.collect()

                logger.info("WebM converted to WAV, pydub modules cleaned up")

                # Use WAV for transcription
                audio_file = BytesIO(wav_bytes)
                audio_file.name = file.filename.replace('.webm', '.wav') if file.filename else "audio.wav"

                # Replace original WebM bytes with WAV bytes for storage
                audio_bytes = wav_bytes

                # Update content type and filename to reflect WAV format
                actual_content_type = "audio/wav"
                actual_filename = audio_file.name
            except Exception as e:
                logger.error(f"WebM to WAV conversion failed: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to convert WebM to WAV: {str(e)}"
                )
        else:
            # Send other formats directly
            audio_file = BytesIO(audio_bytes)
            audio_file.name = file.filename or "audio.wav"

        # Determine response format based on diarization
        # Try verbose_json first (OpenAI standard), fallback to json if not supported
        response_format = "verbose_json" if enable_diarization else "text"

        # Transcribe using Whisper via OpenAI API
        try:
            transcription_response = await client.audio.transcriptions.create(
                model=selected_model,
                file=audio_file,
                response_format=response_format
            )
        except Exception as e:
            # If verbose_json fails, try json format
            error_msg = str(e)
            if enable_diarization and ("verbose_json" in error_msg or "response_format" in error_msg):
                logger.warning(f"verbose_json not supported by vLLM, falling back to json format. Error: {error_msg}")
                response_format = "json"
                audio_file.seek(0)  # Reset file position
                transcription_response = await client.audio.transcriptions.create(
                    model=selected_model,
                    file=audio_file,
                    response_format=response_format
                )
            else:
                raise

        # Log what we got from transcription
        logger.info(f"Transcription API call completed successfully")
        transcription_text_preview = extract_transcription_text(transcription_response)
        logger.info(f"Transcription text preview: '{transcription_text_preview[:200]}'")

        # Perform speaker diarization if enabled
        if enable_diarization:
            try:
                logger.info("Starting speaker diarization...")

                # Perform diarization to identify speaker segments
                diarization_service = get_diarization_service()
                diarization_results = diarization_service.diarize_audio(
                    audio_bytes,
                    num_speakers=num_speakers
                )

                logger.info(f"Diarization found {len(diarization_results)} segments")

                # Check if we have valid results
                if not diarization_results:
                    logger.warning("No speaker segments found in diarization")
                    transcription_text = extract_transcription_text(transcription_response)
                    transcription_text += "\n\n[No speakers detected in audio]"
                else:
                    # Split audio by speaker segments and transcribe each individually
                    logger.info("Transcribing each speaker segment individually")

                    import io
                    import soundfile as sf

                    # Load audio using soundfile
                    audio_data, sample_rate = sf.read(io.BytesIO(audio_bytes))
                    logger.info(f"Loaded audio: sample_rate={sample_rate}, shape={audio_data.shape}")

                    # Process each speaker segment
                    transcribed_segments = []

                    for idx, seg in enumerate(diarization_results):
                        speaker = seg['speaker']
                        start_time = seg['start']
                        end_time = seg['end']
                        duration = end_time - start_time

                        # Skip very short segments (< 0.5 seconds)
                        if duration < 0.5:
                            logger.info(f"Skipping segment {idx+1}: too short ({duration:.2f}s)")
                            continue

                        # Extract audio chunk for this segment
                        start_sample = int(start_time * sample_rate)
                        end_sample = int(end_time * sample_rate)

                        # Handle stereo/mono audio
                        if len(audio_data.shape) == 2:
                            audio_chunk = audio_data[start_sample:end_sample, :]
                        else:
                            audio_chunk = audio_data[start_sample:end_sample]

                        # Write audio chunk to WAV buffer
                        chunk_buffer = io.BytesIO()
                        sf.write(chunk_buffer, audio_chunk, sample_rate, format='WAV')
                        chunk_buffer.seek(0)
                        chunk_buffer.name = f"chunk_{idx}.wav"

                        # Transcribe this segment
                        try:
                            logger.info(
                                f"Transcribing segment {idx+1}/{len(diarization_results)}: "
                                f"{speaker} ({start_time:.1f}s-{end_time:.1f}s, {duration:.1f}s)"
                            )

                            chunk_transcription = await client.audio.transcriptions.create(
                                model=selected_model,
                                file=chunk_buffer,
                                response_format="text"
                            )

                            chunk_text = extract_transcription_text(chunk_transcription).strip()

                            if chunk_text:
                                transcribed_segments.append({
                                    'speaker': speaker,
                                    'text': chunk_text,
                                    'start': start_time,
                                    'end': end_time
                                })
                                logger.info(f"Segment {idx+1} transcribed: '{chunk_text[:50]}...'")
                            else:
                                logger.warning(f"Segment {idx+1} returned empty transcription")

                        except Exception as e:
                            logger.error(f"Failed to transcribe segment {idx+1}: {e}")
                            continue

                    # Format output with speaker labels
                    if transcribed_segments:
                        output_lines = [
                            f"[{seg['speaker']}] {seg['text']} "
                            f"({seg['start']:.1f}s - {seg['end']:.1f}s)"
                            for seg in transcribed_segments
                        ]
                        transcription_text = "\n".join(output_lines)
                        logger.info(f"Successfully transcribed {len(transcribed_segments)} speaker segments")
                    else:
                        logger.warning("No segments were successfully transcribed")
                        transcription_text = extract_transcription_text(transcription_response)
                        transcription_text += "\n\n[Diarization succeeded but segment transcription failed]"

                logger.info("Diarization completed successfully")
            except Exception as e:
                logger.error(f"Diarization failed: {e}", exc_info=True)
                # Fallback to plain text
                transcription_text = extract_transcription_text(transcription_response)
                transcription_text += "\n\n[Diarization failed - transcription only]"
        else:
            # Extract text from response (handle different response formats)
            transcription_text = extract_transcription_text(transcription_response)

        logger.info(f"Transcription completed: {len(transcription_text)} characters")

        # Create database record
        db_transcription = Transcription(
            text=transcription_text,
            audio_data=audio_bytes,
            audio_filename=actual_filename or "audio.wav",
            audio_content_type=actual_content_type or "audio/wav",
            url=url if url and url.strip() else None,
            user_id=current_user.id,
        )

        session.add(db_transcription)
        session.commit()
        session.refresh(db_transcription)

        logger.info(f"Transcription saved with ID: {db_transcription.id}")

        # Return public schema (without binary data)
        return TranscriptionPublic(
            id=db_transcription.id,
            text=db_transcription.text,
            audio_filename=db_transcription.audio_filename,
            audio_content_type=db_transcription.audio_content_type,
            created_at=db_transcription.created_at,
            duration_seconds=db_transcription.duration_seconds,
            priority=db_transcription.priority,
            url=db_transcription.url,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during transcription: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )


@app.get("/api/transcriptions", response_model=TranscriptionList)
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

    Requires authentication. Only returns transcriptions belonging to the authenticated user.

    Args:
        skip: Number of records to skip (offset)
        limit: Maximum number of records to return (defaults to DEFAULT_PAGE_SIZE, max: MAX_PAGE_SIZE)
        priority: Optional priority filter (low, medium, high)
        search: Optional search query (searches in transcription text)
        current_user: Authenticated user
        session: Database session dependency

    Returns:
        TranscriptionList: Paginated list of user's transcriptions
    """
    # Use default page size if not provided
    if limit is None:
        limit = settings.DEFAULT_PAGE_SIZE

    # Enforce maximum page size
    limit = min(limit, settings.MAX_PAGE_SIZE)

    # Build base query - filter by user
    statement = select(Transcription).where(Transcription.user_id == current_user.id)

    # Add priority filter if provided
    if priority:
        statement = statement.where(Transcription.priority == priority)

    # Add search filter if provided (case-insensitive search in text)
    if search:
        search_pattern = f"%{search}%"
        statement = statement.where(Transcription.text.ilike(search_pattern))

    # Get total count with filter
    total = len(session.exec(statement).all())

    # Get paginated results
    statement = (
        statement
        .order_by(Transcription.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    transcriptions = session.exec(statement).all()

    # Convert to public schema
    public_transcriptions = [
        TranscriptionPublic(
            id=t.id,
            text=t.text,
            audio_filename=t.audio_filename,
            audio_content_type=t.audio_content_type,
            created_at=t.created_at,
            duration_seconds=t.duration_seconds,
            priority=t.priority,
            url=t.url,
        )
        for t in transcriptions
    ]

    return TranscriptionList(
        transcriptions=public_transcriptions,
        total=total,
        skip=skip,
        limit=limit,
    )


@app.get("/api/transcriptions/{transcription_id}", response_model=TranscriptionPublic)
def get_transcription(
    transcription_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """
    Get a specific transcription by ID.

    Requires authentication. Only returns transcription if it belongs to the authenticated user.

    Args:
        transcription_id: ID of the transcription
        current_user: Authenticated user
        session: Database session dependency

    Returns:
        TranscriptionPublic: Transcription details

    Raises:
        HTTPException: If transcription not found or doesn't belong to user
    """
    transcription = session.get(Transcription, transcription_id)
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")

    # Verify ownership
    if transcription.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this transcription")

    return TranscriptionPublic(
        id=transcription.id,
        text=transcription.text,
        audio_filename=transcription.audio_filename,
        audio_content_type=transcription.audio_content_type,
        created_at=transcription.created_at,
        duration_seconds=transcription.duration_seconds,
        priority=transcription.priority,
        url=transcription.url,
    )


@app.get("/api/transcriptions/{transcription_id}/audio")
async def get_audio(
    transcription_id: int,
    token: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """
    Download the audio file for a specific transcription.

    Requires authentication via token query parameter (for HTML audio elements).
    Only allows download if transcription belongs to the authenticated user.

    Args:
        transcription_id: ID of the transcription
        token: JWT token as query parameter (required for audio playback)
        session: Database session dependency

    Returns:
        Response: Audio file as binary data

    Raises:
        HTTPException: If transcription not found or doesn't belong to user
    """
    # Authenticate using token from query parameter
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required"
        )

    try:
        from backend.auth import decode_access_token, get_user_by_username
        token_data = decode_access_token(token)
        user = get_user_by_username(session, username=token_data.username)

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or inactive user"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

    transcription = session.get(Transcription, transcription_id)
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")

    # Verify ownership
    if transcription.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this transcription")

    return Response(
        content=transcription.audio_data,
        media_type=transcription.audio_content_type,
        headers={
            "Content-Disposition": f'inline; filename="{transcription.audio_filename}"'
        }
    )


@app.get("/api/transcriptions/{transcription_id}/download")
async def download_transcription(
    transcription_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """
    Download a transcription as a ZIP file containing:
    - USERNAME.wav: Audio file in WAV format
    - config.json: Transcription metadata and text

    Requires authentication. Only allows download if transcription belongs to the authenticated user.

    Args:
        transcription_id: ID of the transcription
        current_user: Authenticated user
        session: Database session dependency

    Returns:
        StreamingResponse: ZIP file containing audio and config

    Raises:
        HTTPException: If transcription not found or doesn't belong to user
    """
    transcription = session.get(Transcription, transcription_id)
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")

    # Verify ownership
    if transcription.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this transcription")

    # Get audio in WAV format (convert if needed)
    try:
        # Check if audio is already in WAV format
        # Check both metadata AND actual file signature (RIFF header)
        is_wav_by_metadata = transcription.audio_content_type == 'audio/wav'
        is_wav_by_signature = transcription.audio_data[:4] == b'RIFF' and transcription.audio_data[8:12] == b'WAVE'

        if is_wav_by_metadata or is_wav_by_signature:
            # Already WAV, no conversion needed
            wav_bytes = transcription.audio_data
            if is_wav_by_signature and not is_wav_by_metadata:
                logger.warning(
                    f"Transcription {transcription_id} has WAV data but incorrect content_type "
                    f"({transcription.audio_content_type}). Using WAV data without conversion."
                )
            else:
                logger.info(f"Audio already in WAV format for transcription {transcription_id}")
        else:
            # Need to convert to WAV
            from backend.audio_converter import convert_audio_to_wav

            # Determine format from content type
            format_mapping = {
                'audio/webm': 'webm',
                'audio/mp3': 'mp3',
                'audio/mpeg': 'mp3',
            }
            input_format = format_mapping.get(transcription.audio_content_type, 'wav')

            # Convert to WAV
            wav_bytes = convert_audio_to_wav(transcription.audio_data, source_format=input_format)

            logger.info(f"Converted audio from {input_format.upper()} to WAV format for transcription {transcription_id}")
    except Exception as e:
        logger.error(f"Error processing audio to WAV: {e}")
        raise HTTPException(status_code=500, detail="Failed to process audio to WAV format")

    # Create config.json content
    wav_filename = f"{current_user.username}.wav"
    config_data = {
        current_user.username: {
            "transcript": transcription.text,
            "audio_file": wav_filename
        }
    }
    config_json = json.dumps(config_data, indent=4)

    # Create ZIP file in memory
    zip_buffer = BytesIO()
    try:
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add WAV file
            zip_file.writestr(wav_filename, wav_bytes)

            # Add config.json
            zip_file.writestr('config.json', config_json)

        zip_buffer.seek(0)
        logger.info(f"Created ZIP archive for transcription {transcription_id}")
    except Exception as e:
        logger.error(f"Error creating ZIP file: {e}")
        raise HTTPException(status_code=500, detail="Failed to create download package")

    # Generate a meaningful filename for the ZIP
    zip_filename = f"transcription_{transcription_id}_{current_user.username}.zip"

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{zip_filename}"'
        }
    )


@app.patch("/api/transcriptions/{transcription_id}", response_model=TranscriptionPublic)
def update_transcription_priority(
    transcription_id: int,
    priority: str,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """
    Update the priority of a transcription.

    Requires authentication. Only allows update if transcription belongs to the authenticated user.

    Args:
        transcription_id: ID of the transcription to update
        priority: New priority value (low, medium, high)
        current_user: Authenticated user
        session: Database session dependency

    Returns:
        TranscriptionPublic: Updated transcription

    Raises:
        HTTPException: If transcription not found or doesn't belong to user
    """
    # Validate priority value
    valid_priorities = [p.value for p in Priority]
    if priority not in valid_priorities:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid priority. Must be one of: {', '.join(valid_priorities)}"
        )

    transcription = session.get(Transcription, transcription_id)
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")

    # Verify ownership
    if transcription.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this transcription")

    transcription.priority = priority
    session.add(transcription)
    session.commit()
    session.refresh(transcription)

    logger.info(f"Updated transcription ID {transcription_id} priority to: {priority}")

    return TranscriptionPublic(
        id=transcription.id,
        text=transcription.text,
        audio_filename=transcription.audio_filename,
        audio_content_type=transcription.audio_content_type,
        created_at=transcription.created_at,
        duration_seconds=transcription.duration_seconds,
        priority=transcription.priority,
        url=transcription.url,
    )


@app.delete("/api/transcriptions/{transcription_id}")
def delete_transcription(
    transcription_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """
    Delete a transcription and its audio file.

    Requires authentication. Only allows deletion if transcription belongs to the authenticated user.

    Args:
        transcription_id: ID of the transcription to delete
        current_user: Authenticated user
        session: Database session dependency

    Returns:
        dict: Success message

    Raises:
        HTTPException: If transcription not found or doesn't belong to user
    """
    transcription = session.get(Transcription, transcription_id)
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")

    # Verify ownership
    if transcription.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this transcription")

    session.delete(transcription)
    session.commit()

    logger.info(f"Deleted transcription ID: {transcription_id}")

    return {"message": "Transcription deleted successfully"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=True,
    )
