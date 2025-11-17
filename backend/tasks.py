"""
Celery tasks for background transcription processing.

This module defines Celery tasks for asynchronous audio transcription
with automatic chunking support for long recordings.

Tasks:
    - transcribe_audio_task: Main transcription task with chunking
    - Handles both regular transcription and diarization modes
    - Updates database with progress and results
    - Implements retry logic for transient failures

Architecture:
    1. Load transcription record from database
    2. Check audio duration
    3. If > 60s: chunk audio and process chunks sequentially
    4. If diarization enabled: use diarization-aware chunking
    5. Merge chunk results
    6. Update database with final transcription
    7. Update status throughout process

Usage:
    from backend.tasks import transcribe_audio_task
    result = transcribe_audio_task.delay(transcription_id=123)
"""

import base64
import json
import logging
from io import BytesIO
from typing import List, Dict

from celery import Task
from openai import AsyncOpenAI
import asyncio

from backend.celery_app import celery_app
from backend.config import settings
from backend.database import get_session
from backend.models import Transcription
from backend.audio_chunker import chunk_audio, chunk_audio_by_diarization
from backend.transcription_merger import merge_transcriptions, group_by_speaker
from backend.diarization import get_diarization_service

logger = logging.getLogger(__name__)


class TranscriptionTask(Task):
    """Base task class with database session management."""

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """Clean up after task completes."""
        # Close any open sessions
        pass


def extract_transcription_text(response) -> str:
    """
    Extract transcription text from various response formats.

    Handles different formats returned by OpenAI-compatible Whisper endpoints:
    - Direct string responses
    - JSON strings containing text
    - Objects with .text attribute
    - Dicts with 'text' key
    - Pydantic models with model_dump()
    """
    # If it's a string, check if it's JSON first
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
    if hasattr(response, 'text'):
        return response.text

    # Handle dict responses
    if isinstance(response, dict) and 'text' in response:
        return response['text']

    # Try to convert to dict if it has model_dump (Pydantic model)
    if hasattr(response, 'model_dump'):
        data = response.model_dump()
        if 'text' in data:
            return data['text']

    # Fallback: convert to string
    logger.warning(f"Unexpected response format: {type(response)}, converting to string")
    return str(response)


@celery_app.task(
    bind=True,
    base=TranscriptionTask,
    name='backend.tasks.transcribe_audio',
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3},
    time_limit=3600,  # 1 hour hard limit
    soft_time_limit=3300  # 55 minutes soft limit
)
def transcribe_audio_task(
    self,
    transcription_id: int,
    model: str,
    enable_diarization: bool = False,
    num_speakers: int | None = None
):
    """
    Process audio transcription with automatic chunking for long recordings.

    This task handles the complete transcription pipeline:
    1. Load audio from database
    2. Determine if chunking is needed
    3. For long audio: chunk, transcribe chunks, merge results
    4. For diarization: use speaker-aware chunking
    5. Update database with results and status

    Args:
        self: Celery task instance (bound)
        transcription_id: Database ID of transcription record
        model: Whisper model name to use
        enable_diarization: Enable speaker diarization
        num_speakers: Number of speakers (optional, auto-detect if None)

    Returns:
        Dictionary with transcription results and metadata

    Raises:
        Exception: For critical errors that prevent transcription
    """
    logger.info(f"Starting transcription task for ID: {transcription_id} (model={model}, diarization={enable_diarization})")

    # Update task state to PROCESSING
    self.update_state(state='PROCESSING', meta={'status': 'Starting transcription', 'progress': 0})

    session = next(get_session())

    try:
        # Load transcription from database
        db_transcription = session.query(Transcription).filter(Transcription.id == transcription_id).first()
        if not db_transcription:
            raise ValueError(f"Transcription {transcription_id} not found")

        # Update status to processing
        db_transcription.status = "processing"
        db_transcription.progress = 5
        session.commit()

        logger.info(f"Loaded transcription {transcription_id}: {len(db_transcription.audio_data)} bytes")

        audio_bytes = db_transcription.audio_data
        audio_content_type = db_transcription.audio_content_type

        # Determine audio format
        format_mapping = {
            'audio/wav': 'wav',
            'audio/wave': 'wav',
            'audio/x-wav': 'wav',
            'audio/webm': 'webm',
            'audio/mpeg': 'mp3',
            'audio/mp3': 'mp3',
        }
        audio_format = format_mapping.get(audio_content_type, 'wav')

        # Get audio duration and check if chunking needed
        from pydub import AudioSegment
        audio = AudioSegment.from_file(BytesIO(audio_bytes), format=audio_format)
        duration_seconds = len(audio) / 1000.0

        logger.info(f"Audio duration: {duration_seconds:.2f}s")

        # Update progress
        db_transcription.progress = 10
        session.commit()
        self.update_state(state='PROCESSING', meta={'status': 'Audio loaded', 'progress': 10})

        # Validate model
        if model not in settings.MODELS:
            raise ValueError(f"Invalid model: {model}")

        # Get model URL and create OpenAI client
        model_base_url = settings.get_model_url(model)

        # Use sync run to execute async code
        transcription_text = asyncio.run(
            process_transcription_async(
                self=self,
                session=session,
                db_transcription=db_transcription,
                audio_bytes=audio_bytes,
                audio_format=audio_format,
                duration_seconds=duration_seconds,
                model=model,
                model_base_url=model_base_url,
                enable_diarization=enable_diarization,
                num_speakers=num_speakers
            )
        )

        # Save final transcription
        db_transcription.text = transcription_text
        db_transcription.status = "completed"
        db_transcription.progress = 100
        db_transcription.error_message = None
        session.commit()

        logger.info(f"Transcription {transcription_id} completed successfully: {len(transcription_text)} characters")

        return {
            'transcription_id': transcription_id,
            'status': 'completed',
            'text_length': len(transcription_text),
            'duration_seconds': duration_seconds
        }

    except Exception as e:
        logger.error(f"Transcription task failed for ID {transcription_id}: {e}", exc_info=True)

        # Update database with error
        try:
            db_transcription = session.query(Transcription).filter(Transcription.id == transcription_id).first()
            if db_transcription:
                db_transcription.status = "failed"
                db_transcription.error_message = str(e)
                db_transcription.progress = 0

                # Save error message in text field if no transcription yet
                if not db_transcription.text or db_transcription.text.strip() == "":
                    db_transcription.text = f"[TRANSCRIPTION FAILED]\n\nError: {str(e)}\n\nThe audio recording has been saved but could not be transcribed."

                session.commit()
        except Exception as db_error:
            logger.error(f"Failed to update error status in database: {db_error}")

        raise

    finally:
        session.close()


async def process_transcription_async(
    self,
    session,
    db_transcription,
    audio_bytes: bytes,
    audio_format: str,
    duration_seconds: float,
    model: str,
    model_base_url: str,
    enable_diarization: bool,
    num_speakers: int | None
) -> str:
    """
    Async function to process transcription with chunking support.

    Handles both regular transcription and diarization modes.
    """
    client = AsyncOpenAI(base_url=model_base_url, api_key=settings.API_KEY)

    try:
        chunk_duration = settings.CHUNK_DURATION_SECONDS

        # Case 1: Diarization enabled
        if enable_diarization:
                logger.info("Diarization enabled, performing speaker diarization first")
        
                self.update_state(state='PROCESSING', meta={'status': 'Performing diarization', 'progress': 15})
                db_transcription.progress = 15
                session.commit()
        
                # Perform diarization
                diarization_service = get_diarization_service()
                diarization_results = diarization_service.diarize_audio(audio_bytes, num_speakers=num_speakers)

                # CRITICAL FIX: Sort segments by start time to ensure chronological order
                # Pyannote may return segments in speaker-clustering order, not temporal order
                # Without sorting, sentences can appear out of sequence in the final transcription
                diarization_results = sorted(diarization_results, key=lambda x: x['start'])

                logger.info(f"Diarization found {len(diarization_results)} segments (sorted chronologically)")
        
                self.update_state(state='PROCESSING', meta={'status': 'Diarization complete', 'progress': 30})
                db_transcription.progress = 30
                session.commit()
        
                if not diarization_results:
                    logger.warning("No speaker segments found")
                    # Fall back to simple transcription
                    audio_file = BytesIO(audio_bytes)
                    audio_file.name = "audio.wav"
                    response = await client.audio.transcriptions.create(
                        model=model,
                        file=audio_file,
                        response_format="text"
                    )
                    return extract_transcription_text(response) + "\n\n[No speakers detected]"
        
                # Chunk by diarization (will sub-chunk if segments are too long)
                chunks = chunk_audio_by_diarization(
                    audio_bytes,
                    diarization_results,
                    max_chunk_duration=chunk_duration,
                    source_format=audio_format
                )
        
                logger.info(f"Created {len(chunks)} diarization-aware chunks")
        
                # Transcribe each chunk
                transcribed_chunks = []
                progress_step = 60 / len(chunks)  # Progress from 30% to 90%
        
                for idx, (chunk_bytes, start_time, end_time, speaker) in enumerate(chunks):
                    logger.info(f"Transcribing chunk {idx+1}/{len(chunks)}: {speaker} {start_time:.2f}s-{end_time:.2f}s")
        
                    progress = int(30 + (idx * progress_step))
                    self.update_state(
                        state='PROCESSING',
                        meta={'status': f'Transcribing chunk {idx+1}/{len(chunks)}', 'progress': progress}
                    )
                    db_transcription.progress = progress
                    session.commit()
        
                    try:
                        audio_file = BytesIO(chunk_bytes)
                        audio_file.name = "chunk.wav"
        
                        response = await client.audio.transcriptions.create(
                            model=model,
                            file=audio_file,
                            response_format="text"
                        )
        
                        text = extract_transcription_text(response)
        
                        if text.strip():
                            transcribed_chunks.append({
                                'text': text,
                                'start': start_time,
                                'end': end_time,
                                'speaker': speaker
                            })
                            logger.debug(f"Chunk {idx+1} transcribed: {len(text)} chars")
                        else:
                            logger.warning(f"Chunk {idx+1} returned empty transcription")
        
                    except Exception as e:
                        logger.error(f"Failed to transcribe chunk {idx+1}: {e}")
                        # Continue with other chunks
                        continue
        
                if not transcribed_chunks:
                    raise Exception("All diarization chunks failed to transcribe")
        
                # Group consecutive chunks by speaker and merge
                grouped_chunks = group_by_speaker(transcribed_chunks)
                transcription_text = merge_transcriptions(grouped_chunks, include_speakers=True)
        
                logger.info(f"Merged {len(transcribed_chunks)} chunks into final transcription")
                return transcription_text
        
        # Case 2: Regular transcription (possibly with chunking)
        elif duration_seconds > chunk_duration:
                # Need to chunk
                logger.info(f"Audio is {duration_seconds:.2f}s, chunking into {chunk_duration}s segments")
        
                chunks = chunk_audio(audio_bytes, chunk_duration_seconds=chunk_duration, source_format=audio_format)
                logger.info(f"Created {len(chunks)} time-based chunks")
        
                self.update_state(state='PROCESSING', meta={'status': 'Audio chunked', 'progress': 20})
                db_transcription.progress = 20
                session.commit()
        
                # Transcribe each chunk
                transcribed_chunks = []
                progress_step = 70 / len(chunks)  # Progress from 20% to 90%
        
                for idx, (chunk_bytes, start_time, end_time) in enumerate(chunks):
                    logger.info(f"Transcribing chunk {idx+1}/{len(chunks)}: {start_time:.2f}s-{end_time:.2f}s")
        
                    progress = int(20 + (idx * progress_step))
                    self.update_state(
                        state='PROCESSING',
                        meta={'status': f'Transcribing chunk {idx+1}/{len(chunks)}', 'progress': progress}
                    )
                    db_transcription.progress = progress
                    session.commit()
        
                    try:
                        audio_file = BytesIO(chunk_bytes)
                        audio_file.name = "chunk.wav"
        
                        response = await client.audio.transcriptions.create(
                            model=model,
                            file=audio_file,
                            response_format="text"
                        )
        
                        text = extract_transcription_text(response)
        
                        if text.strip():
                            transcribed_chunks.append({
                                'text': text,
                                'start': start_time,
                                'end': end_time
                            })
                            logger.debug(f"Chunk {idx+1} transcribed: {len(text)} chars")
                        else:
                            logger.warning(f"Chunk {idx+1} returned empty transcription")
        
                    except Exception as e:
                        logger.error(f"Failed to transcribe chunk {idx+1}: {e}")
                        # Continue with other chunks
                        continue
        
                if not transcribed_chunks:
                    raise Exception("All chunks failed to transcribe")
        
                # Merge chunks
                transcription_text = merge_transcriptions(transcribed_chunks, include_timestamps=False)
        
                logger.info(f"Merged {len(transcribed_chunks)} chunks into final transcription")
                return transcription_text
        
        else:
                # Short audio, no chunking needed
                logger.info(f"Audio is {duration_seconds:.2f}s, no chunking needed")
        
                self.update_state(state='PROCESSING', meta={'status': 'Transcribing audio', 'progress': 50})
                db_transcription.progress = 50
                session.commit()
        
                audio_file = BytesIO(audio_bytes)
                audio_file.name = "audio.wav"
        
                response = await client.audio.transcriptions.create(
                    model=model,
                    file=audio_file,
                    response_format="text"
                )
        
                transcription_text = extract_transcription_text(response)
                logger.info(f"Transcription completed: {len(transcription_text)} characters")

                return transcription_text
    finally:
        # Properly close the async client before event loop closes
        await client.close()


# ============================================================================
# Scheduled Tasks
# ============================================================================

@celery_app.task(name="reset_daily_quotas")
def reset_daily_quotas_task():
    """
    Reset all users' daily quotas at midnight UTC.

    This task runs on a schedule (configured in celery_app.py) to reset
    the daily AI action quota for all users.

    Returns:
        dict: Summary of reset operation
    """
    from backend.services.permission_service import PermissionService
    from backend.logging_config import get_logger, get_security_logger

    logger = get_logger(__name__)
    security_logger = get_security_logger()

    logger.info("Starting daily quota reset task")

    try:
        with get_session() as session:
            count = PermissionService.reset_daily_quotas(session)
            logger.info(f"Daily quota reset completed for {count} users")

            return {
                "status": "success",
                "users_reset": count,
                "timestamp": __import__('datetime').datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error(f"Error resetting daily quotas: {str(e)}", exc_info=True)
        security_logger.error(
            "Daily quota reset failed",
            extra={
                "event_type": "quota_reset_failed",
                "error": str(e)
            }
        )
        raise
