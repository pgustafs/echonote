"""
Transcription Service Layer

This module contains all business logic for transcription operations,
separated from the API layer for better testability and maintainability.

Following the Service Layer pattern, this module handles:
- Audio file validation and processing
- Transcription creation and management
- File format conversion
- ZIP packaging for downloads
- Database operations for transcriptions
"""

import io
import json
import logging
import zipfile
from io import BytesIO
from typing import Optional

from fastapi import HTTPException, UploadFile
from sqlmodel import Session, select

from backend.config import settings
from backend.models import Priority, Transcription, TranscriptionPublic, User
from backend.services.minio_service import get_minio_service, generate_object_name

# Configure logger
logger = logging.getLogger(__name__)


class TranscriptionService:
    """
    Service class for handling transcription-related business logic.

    This class encapsulates all transcription operations, making them
    reusable and testable independently of the API layer.
    """

    @staticmethod
    def validate_audio_file(file: UploadFile) -> None:
        """
        Validate uploaded audio file type.

        Args:
            file: The uploaded file to validate

        Raises:
            HTTPException: If file type is not allowed
        """
        if file.content_type not in settings.ALLOWED_AUDIO_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid audio type. Allowed types: {settings.ALLOWED_AUDIO_TYPES}"
            )

    @staticmethod
    def validate_audio_size(audio_bytes: bytes) -> None:
        """
        Validate audio file size.

        Args:
            audio_bytes: Audio file binary data

        Raises:
            HTTPException: If file is too large
        """
        if len(audio_bytes) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE} bytes"
            )

    @staticmethod
    def get_audio_duration(audio_bytes: bytes) -> Optional[float]:
        """
        Extract audio duration from binary data.

        Args:
            audio_bytes: Audio file binary data

        Returns:
            Duration in seconds, or None if unable to determine
        """
        try:
            import soundfile as sf
            audio_data, sample_rate = sf.read(io.BytesIO(audio_bytes))
            duration_seconds = len(audio_data) / sample_rate
            return duration_seconds
        except Exception as e:
            logger.warning(f"Could not determine audio duration: {e}")
            return None

    @staticmethod
    def validate_audio_duration(duration_seconds: Optional[float]) -> None:
        """
        Validate audio duration against maximum allowed.

        Args:
            duration_seconds: Audio duration in seconds

        Raises:
            HTTPException: If audio is too long
        """
        if duration_seconds and duration_seconds > settings.MAX_AUDIO_DURATION_SECONDS:
            raise HTTPException(
                status_code=400,
                detail=f"Audio too long. Maximum duration: {settings.MAX_AUDIO_DURATION_SECONDS} seconds ({settings.MAX_AUDIO_DURATION_SECONDS/60:.1f} minutes)"
            )

    # NOTE: WebM→WAV conversion has been moved to worker (tasks.py)
    # This keeps the backend container lightweight without audio processing dependencies

    @staticmethod
    async def process_audio_upload(
        file: UploadFile,
        model: Optional[str] = None
    ) -> tuple[bytes, str, str, Optional[float]]:
        """
        Process uploaded audio file (validation, conversion, duration extraction).

        Args:
            file: The uploaded audio file
            model: Model name to validate (optional)

        Returns:
            Tuple of (audio_bytes, content_type, filename, duration_seconds)

        Raises:
            HTTPException: If validation or processing fails
        """
        # Validate model if provided
        selected_model = model if model else settings.DEFAULT_MODEL
        if selected_model not in settings.MODELS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid model: {selected_model}. Available models: {list(settings.MODELS.keys())}"
            )

        # Validate file type
        TranscriptionService.validate_audio_file(file)

        # Read audio file
        audio_bytes = await file.read()
        original_size_mb = len(audio_bytes) / (1024 * 1024)

        # Validate file size
        TranscriptionService.validate_audio_size(audio_bytes)

        logger.info(f"Processing audio upload: {file.filename}")
        logger.info(f"File size: {len(audio_bytes)} bytes ({original_size_mb:.2f} MB)")
        logger.info(f"Content type: {file.content_type}")
        logger.info(f"Model: {selected_model}")

        # Get audio duration
        duration_seconds = TranscriptionService.get_audio_duration(audio_bytes)
        if duration_seconds:
            duration_minutes = duration_seconds / 60
            logger.info(f"Audio duration: {duration_seconds:.2f} seconds ({duration_minutes:.2f} minutes)")

        # Validate duration
        TranscriptionService.validate_audio_duration(duration_seconds)

        # Store audio as-is (conversion will happen in worker if needed)
        # This keeps the backend lightweight - no audio processing dependencies
        actual_content_type = file.content_type
        actual_filename = file.filename

        return audio_bytes, actual_content_type, actual_filename, duration_seconds

    @staticmethod
    def create_transcription_record(
        session: Session,
        audio_bytes: bytes,
        audio_filename: str,
        audio_content_type: str,
        duration_seconds: Optional[float],
        url: Optional[str],
        user: User
    ) -> Transcription:
        """
        Create a new transcription database record with pending status.
        Uploads audio file to MinIO object storage instead of storing in database.

        Args:
            session: Database session
            audio_bytes: Audio file binary data
            audio_filename: Original filename
            audio_content_type: MIME type
            duration_seconds: Audio duration
            url: Optional associated URL
            user: Owner user

        Returns:
            Created transcription record
        """
        # Create initial record to get ID
        db_transcription = Transcription(
            text="",  # Will be filled by background task
            audio_data=None,  # No longer storing in database
            audio_filename=audio_filename,
            audio_content_type=audio_content_type,
            duration_seconds=duration_seconds,
            url=url if url and url.strip() else None,
            user_id=user.id,
            status="pending",
            progress=0
        )

        session.add(db_transcription)
        session.commit()
        session.refresh(db_transcription)

        # Upload audio to MinIO
        try:
            minio_service = get_minio_service()
            object_name = generate_object_name(user.id, db_transcription.id, audio_filename)
            minio_service.upload_audio(audio_bytes, object_name, audio_content_type)

            # Update record with MinIO path
            db_transcription.minio_object_path = object_name
            session.commit()
            session.refresh(db_transcription)

            logger.info(
                f"Created transcription record ID: {db_transcription.id} "
                f"(status=pending, minio_path={object_name})"
            )
            return db_transcription

        except Exception as e:
            # Rollback database record if MinIO upload fails
            logger.error(f"Failed to upload audio to MinIO: {e}")
            session.delete(db_transcription)
            session.commit()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload audio file to storage: {str(e)}"
            )

    @staticmethod
    def dispatch_transcription_task(
        transcription_id: int,
        model: str,
        enable_diarization: bool,
        num_speakers: Optional[int],
        session: Session
    ) -> str:
        """
        Dispatch Celery background task for transcription processing.

        Args:
            transcription_id: ID of transcription to process
            model: Model name to use
            enable_diarization: Whether to enable speaker diarization
            num_speakers: Number of speakers (optional)
            session: Database session

        Returns:
            Task ID

        Raises:
            HTTPException: If task dispatch fails
        """
        # Import celery_app to dispatch task by name (avoids importing worker code)
        from backend.celery_app import celery_app

        transcription = session.get(Transcription, transcription_id)
        if not transcription:
            raise HTTPException(status_code=404, detail="Transcription not found")

        try:
            # Use send_task to dispatch by name without importing task function
            # This keeps backend lightweight - no worker dependencies needed
            task_result = celery_app.send_task(
                'backend.tasks.transcribe_audio',
                kwargs={
                    'transcription_id': transcription_id,
                    'model': model,
                    'enable_diarization': enable_diarization,
                    'num_speakers': num_speakers
                }
            )

            # Save task ID
            transcription.task_id = task_result.id
            session.commit()

            logger.info(f"Dispatched transcription task {task_result.id} for transcription {transcription_id}")
            return task_result.id

        except Exception as e:
            logger.error(f"Failed to dispatch Celery task: {e}", exc_info=True)
            # Update status to failed
            transcription.status = "failed"
            transcription.error_message = f"Failed to start background task: {str(e)}"
            session.commit()

            raise HTTPException(
                status_code=500,
                detail=f"Failed to start transcription task: {str(e)}"
            )

    @staticmethod
    def get_user_transcriptions(
        session: Session,
        user: User,
        skip: int = 0,
        limit: Optional[int] = None,
        priority: Optional[str] = None,
        search: Optional[str] = None
    ) -> tuple[list[Transcription], int]:
        """
        Get paginated list of user's transcriptions with optional filters.

        Args:
            session: Database session
            user: User to get transcriptions for
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            priority: Optional priority filter
            search: Optional text search query

        Returns:
            Tuple of (transcriptions list, total count)
        """
        # Use default page size if not provided
        if limit is None:
            limit = settings.DEFAULT_PAGE_SIZE

        # Enforce maximum page size
        limit = min(limit, settings.MAX_PAGE_SIZE)

        # Build base query - filter by user
        statement = select(Transcription).where(Transcription.user_id == user.id)

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

        return transcriptions, total

    @staticmethod
    def get_transcription_by_id(
        session: Session,
        transcription_id: int,
        user: User
    ) -> Transcription:
        """
        Get a specific transcription by ID, verifying ownership.

        Args:
            session: Database session
            transcription_id: ID of the transcription
            user: User requesting the transcription

        Returns:
            Transcription record

        Raises:
            HTTPException: If not found or not authorized
        """
        transcription = session.get(Transcription, transcription_id)
        if not transcription:
            raise HTTPException(status_code=404, detail="Transcription not found")

        # Verify ownership
        if transcription.user_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this transcription")

        return transcription

    @staticmethod
    def update_transcription_priority(
        session: Session,
        transcription_id: int,
        priority: str,
        user: User
    ) -> Transcription:
        """
        Update the priority of a transcription.

        Args:
            session: Database session
            transcription_id: ID of the transcription
            priority: New priority value
            user: User making the update

        Returns:
            Updated transcription

        Raises:
            HTTPException: If validation fails or not authorized
        """
        # Validate priority value
        valid_priorities = [p.value for p in Priority]
        if priority not in valid_priorities:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid priority. Must be one of: {', '.join(valid_priorities)}"
            )

        transcription = TranscriptionService.get_transcription_by_id(session, transcription_id, user)

        transcription.priority = priority
        session.add(transcription)
        session.commit()
        session.refresh(transcription)

        logger.info(f"Updated transcription ID {transcription_id} priority to: {priority}")
        return transcription

    @staticmethod
    def delete_transcription(
        session: Session,
        transcription_id: int,
        user: User
    ) -> None:
        """
        Delete a transcription and its audio file from both database and MinIO storage.

        Args:
            session: Database session
            transcription_id: ID of the transcription
            user: User requesting deletion

        Raises:
            HTTPException: If not found or not authorized
        """
        transcription = TranscriptionService.get_transcription_by_id(session, transcription_id, user)

        # Delete audio file from MinIO if it exists
        if transcription.minio_object_path:
            try:
                minio_service = get_minio_service()
                minio_service.delete_audio(transcription.minio_object_path)
                logger.info(f"Deleted audio from MinIO: {transcription.minio_object_path}")
            except Exception as e:
                # Log error but don't fail the deletion - database cleanup should continue
                logger.warning(
                    f"Failed to delete audio from MinIO for transcription {transcription_id}: {e}"
                )

        # Delete database record
        session.delete(transcription)
        session.commit()

        logger.info(f"Deleted transcription ID: {transcription_id}")

    @staticmethod
    def delete_audio_from_storage(
        user_id: int,
        transcription_id: int,
        filename: str
    ) -> None:
        """
        Delete only the audio file from MinIO storage.

        This method removes the audio file from MinIO but does not delete
        the transcription record from the database. Used when user wants
        to save storage space but keep the transcription text.

        Args:
            user_id: ID of the user who owns the transcription
            transcription_id: ID of the transcription
            filename: Name of the audio file

        Raises:
            Exception: If MinIO deletion fails
        """
        # Construct the MinIO object path
        object_path = f"audio/user_{user_id}/transcription_{transcription_id}_{filename}"

        try:
            minio_service = get_minio_service()
            minio_service.delete_audio(object_path)
            logger.info(f"Deleted audio from MinIO: {object_path}")
        except Exception as e:
            logger.error(f"Failed to delete audio from MinIO: {object_path}, error: {e}")
            raise

    @staticmethod
    def convert_audio_to_wav(
        audio_data: bytes,
        content_type: str,
        transcription_id: int
    ) -> bytes:
        """
        Convert audio to WAV format for download.

        This method dispatches conversion to the Celery worker to keep the backend
        lightweight without audio processing dependencies.

        Args:
            audio_data: Original audio binary data (unused, kept for API compatibility)
            content_type: MIME type of audio
            transcription_id: ID for logging and worker task

        Returns:
            WAV audio bytes

        Raises:
            HTTPException: If conversion fails
        """
        from backend.celery_app import celery_app

        try:
            # Check if audio is already in WAV format
            # Check both metadata AND actual file signature (RIFF header)
            is_wav_by_metadata = content_type == 'audio/wav'
            is_wav_by_signature = audio_data[:4] == b'RIFF' and audio_data[8:12] == b'WAVE'

            if is_wav_by_metadata or is_wav_by_signature:
                # Already WAV, no conversion needed
                if is_wav_by_signature and not is_wav_by_metadata:
                    logger.warning(
                        f"Transcription {transcription_id} has WAV data but incorrect content_type "
                        f"({content_type}). Using WAV data without conversion."
                    )
                else:
                    logger.info(f"Audio already in WAV format for transcription {transcription_id}")
                return audio_data
            else:
                # Need to convert to WAV - dispatch to celery worker
                logger.info(f"Dispatching WAV conversion to worker for transcription {transcription_id}")

                # Dispatch synchronous celery task to worker for conversion
                # Worker has all audio processing dependencies (pydub, ffmpeg)
                task_result = celery_app.send_task(
                    'backend.tasks.convert_audio_format',
                    kwargs={
                        'transcription_id': transcription_id,
                        'target_format': 'wav'
                    }
                )

                # Wait for conversion to complete (timeout 60s)
                wav_bytes = task_result.get(timeout=60)

                logger.info(f"WAV conversion completed for transcription {transcription_id}")
                return wav_bytes
        except Exception as e:
            logger.error(f"Error processing audio to WAV: {e}")
            raise HTTPException(status_code=500, detail="Failed to process audio to WAV format")

    @staticmethod
    def create_download_package(
        transcription: Transcription,
        username: str,
        format: str = 'wav'
    ) -> BytesIO:
        """
        Create a ZIP package containing audio and metadata for download.

        The package includes:
        - {username}.{format}: Audio file in specified format
        - config.json: Transcription metadata and text

        Args:
            transcription: Transcription to package
            username: Username for filename
            format: Audio format (webm, wav, mp3). Defaults to wav.

        Returns:
            BytesIO buffer containing the ZIP file

        Raises:
            HTTPException: If package creation fails
        """
        from backend.celery_app import celery_app

        # Determine source format
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

        # Check if format conversion is needed
        target_format = format.lower()
        if target_format != source_format:
            logger.info(f"Format conversion for download: {source_format} -> {target_format}")
            # Use celery task for conversion
            try:
                task_result = celery_app.send_task(
                    'backend.tasks.convert_audio_format',
                    kwargs={
                        'transcription_id': transcription.id,
                        'target_format': target_format
                    }
                )
                # Wait for conversion to complete (timeout 60s)
                audio_bytes = task_result.get(timeout=60)
            except Exception as e:
                logger.error(f"Format conversion failed for download: {e}")
                raise HTTPException(status_code=500, detail=f"Format conversion failed: {str(e)}")
        else:
            # No conversion needed, get original audio
            if transcription.minio_object_path:
                # New: Fetch from MinIO
                try:
                    minio_service = get_minio_service()
                    audio_bytes = minio_service.download_audio(transcription.minio_object_path)
                except Exception as e:
                    logger.error(f"Failed to download audio from MinIO: {e}")
                    raise HTTPException(status_code=500, detail="Failed to retrieve audio file for download")
            elif transcription.audio_data:
                # Legacy: Use database BLOB
                audio_bytes = transcription.audio_data
            else:
                raise HTTPException(status_code=404, detail="Audio file not found")

        # Create config.json content with correct filename
        audio_filename = f"{username}.{target_format}"
        config_data = {
            username: {
                "transcript": transcription.text,
                "audio_file": audio_filename
            }
        }
        config_json = json.dumps(config_data, indent=4)

        # Create ZIP file in memory
        zip_buffer = BytesIO()
        try:
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add audio file with correct extension
                zip_file.writestr(audio_filename, audio_bytes)

                # Add config.json
                zip_file.writestr('config.json', config_json)

            zip_buffer.seek(0)
            logger.info(f"Created ZIP archive for transcription {transcription.id} with format {target_format}")
            return zip_buffer
        except Exception as e:
            logger.error(f"Error creating ZIP file: {e}")
            raise HTTPException(status_code=500, detail="Failed to create download package")

    @staticmethod
    def to_public_schema(transcription: Transcription) -> TranscriptionPublic:
        """
        Convert database model to public API schema.

        Args:
            transcription: Database transcription record

        Returns:
            Public schema without binary audio data
        """
        return TranscriptionPublic(
            id=transcription.id,
            text=transcription.text,
            audio_filename=transcription.audio_filename,
            audio_content_type=transcription.audio_content_type,
            created_at=transcription.created_at,
            duration_seconds=transcription.duration_seconds,
            priority=transcription.priority,
            url=transcription.url,
            task_id=transcription.task_id,
            status=transcription.status,
            progress=transcription.progress,
            error_message=transcription.error_message,
        )
