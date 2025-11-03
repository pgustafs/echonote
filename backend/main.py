"""
EchoNote FastAPI Backend

A modern voice transcription API that stores audio recordings and their
transcriptions using Whisper (via vLLM) and SQLModel.
"""

import json
import logging
from io import BytesIO
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from openai import AsyncOpenAI
from sqlmodel import Session, select

from backend.config import settings
from backend.database import create_db_and_tables, get_session
from backend.models import Priority, Transcription, TranscriptionList, TranscriptionPublic

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

# Initialize OpenAI client for Whisper API
client = AsyncOpenAI(
    base_url=settings.MODEL_URL,
    api_key=settings.API_KEY,
)
logger.info(f"Initialized OpenAI client with URL: {settings.MODEL_URL}")


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


@app.post("/api/transcribe", response_model=TranscriptionPublic)
async def transcribe_audio(
    file: Annotated[UploadFile, File(description="Audio file to transcribe")],
    url: Annotated[str | None, Form(description="Optional URL associated with the voice note")] = None,
    session: Session = Depends(get_session)
):
    """
    Transcribe an audio file and store it in the database.

    Args:
        file: Audio file uploaded via multipart/form-data
        url: Optional URL associated with the voice note
        session: Database session dependency

    Returns:
        TranscriptionPublic: Created transcription without binary data
    """
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

        # Prepare audio file for Whisper API
        # Frontend converts to WAV format, so we can send directly
        audio_file = BytesIO(audio_bytes)
        audio_file.name = file.filename or "audio.wav"

        # Transcribe using Whisper via OpenAI API
        transcription_response = await client.audio.transcriptions.create(
            model=settings.MODEL_NAME,
            file=audio_file,
            response_format="text"
        )

        # Extract text from response (handle different response formats)
        transcription_text = extract_transcription_text(transcription_response)

        logger.info(f"Transcription completed: {len(transcription_text)} characters")

        # Create database record
        db_transcription = Transcription(
            text=transcription_text,
            audio_data=audio_bytes,
            audio_filename=file.filename or "audio.wav",
            audio_content_type=file.content_type or "audio/wav",
            url=url if url and url.strip() else None,
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
    limit: int = 50,
    priority: str | None = None,
    session: Session = Depends(get_session)
):
    """
    List all transcriptions with pagination and optional priority filtering.

    Args:
        skip: Number of records to skip (offset)
        limit: Maximum number of records to return
        priority: Optional priority filter (low, medium, high)
        session: Database session dependency

    Returns:
        TranscriptionList: Paginated list of transcriptions
    """
    # Build base query
    statement = select(Transcription)

    # Add priority filter if provided
    if priority:
        statement = statement.where(Transcription.priority == priority)

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
    session: Session = Depends(get_session)
):
    """
    Get a specific transcription by ID.

    Args:
        transcription_id: ID of the transcription
        session: Database session dependency

    Returns:
        TranscriptionPublic: Transcription details
    """
    transcription = session.get(Transcription, transcription_id)
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")

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
def get_audio(
    transcription_id: int,
    session: Session = Depends(get_session)
):
    """
    Download the audio file for a specific transcription.

    Args:
        transcription_id: ID of the transcription
        session: Database session dependency

    Returns:
        Response: Audio file as binary data
    """
    transcription = session.get(Transcription, transcription_id)
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")

    return Response(
        content=transcription.audio_data,
        media_type=transcription.audio_content_type,
        headers={
            "Content-Disposition": f'inline; filename="{transcription.audio_filename}"'
        }
    )


@app.patch("/api/transcriptions/{transcription_id}", response_model=TranscriptionPublic)
def update_transcription_priority(
    transcription_id: int,
    priority: str,
    session: Session = Depends(get_session)
):
    """
    Update the priority of a transcription.

    Args:
        transcription_id: ID of the transcription to update
        priority: New priority value (low, medium, high)
        session: Database session dependency

    Returns:
        TranscriptionPublic: Updated transcription
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
    session: Session = Depends(get_session)
):
    """
    Delete a transcription and its audio file.

    Args:
        transcription_id: ID of the transcription to delete
        session: Database session dependency

    Returns:
        dict: Success message
    """
    transcription = session.get(Transcription, transcription_id)
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")

    session.delete(transcription)
    session.commit()

    logger.info(f"Deleted transcription ID: {transcription_id}")

    return {"message": "Transcription deleted successfully"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=True,
    )
