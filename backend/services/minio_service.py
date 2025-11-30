"""
MinIO Object Storage Service

Handles all audio file uploads/downloads to MinIO S3-compatible storage.
Replaces storing audio BLOBs directly in PostgreSQL.
"""

import os
import io
import logging
from datetime import timedelta
from typing import Optional, BinaryIO
from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)

# MinIO Configuration from environment variables
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "echonote-audio")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"


class MinIOService:
    """Service for managing audio files in MinIO object storage"""

    def __init__(self):
        """Initialize MinIO client and ensure bucket exists"""
        try:
            self.client = Minio(
                MINIO_ENDPOINT,
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=MINIO_SECURE
            )

            # Create bucket if it doesn't exist
            if not self.client.bucket_exists(MINIO_BUCKET):
                self.client.make_bucket(MINIO_BUCKET)
                logger.info(f"Created MinIO bucket: {MINIO_BUCKET}")
            else:
                logger.info(f"MinIO bucket already exists: {MINIO_BUCKET}")

        except S3Error as e:
            logger.error(f"Failed to initialize MinIO client: {e}")
            raise

    def upload_audio(
        self,
        file_data: bytes,
        object_name: str,
        content_type: str = "audio/webm"
    ) -> str:
        """
        Upload audio file to MinIO

        Args:
            file_data: Audio file bytes
            object_name: Unique object name (e.g., "audio/user123/recording_456.webm")
            content_type: MIME type of the audio file

        Returns:
            str: Object path in MinIO (bucket/object_name)
        """
        try:
            # Convert bytes to BytesIO stream
            file_stream = io.BytesIO(file_data)
            file_size = len(file_data)

            # Upload to MinIO
            self.client.put_object(
                bucket_name=MINIO_BUCKET,
                object_name=object_name,
                data=file_stream,
                length=file_size,
                content_type=content_type
            )

            logger.info(f"Uploaded audio to MinIO: {object_name} ({file_size} bytes)")
            return f"{MINIO_BUCKET}/{object_name}"

        except S3Error as e:
            logger.error(f"Failed to upload audio to MinIO: {e}")
            raise

    def download_audio(self, object_name: str) -> bytes:
        """
        Download audio file from MinIO

        Args:
            object_name: Object name to download

        Returns:
            bytes: Audio file data
        """
        try:
            response = self.client.get_object(MINIO_BUCKET, object_name)
            data = response.read()
            response.close()
            response.release_conn()

            logger.info(f"Downloaded audio from MinIO: {object_name} ({len(data)} bytes)")
            return data

        except S3Error as e:
            logger.error(f"Failed to download audio from MinIO: {e}")
            raise

    def delete_audio(self, object_name: str) -> None:
        """
        Delete audio file from MinIO

        Args:
            object_name: Object name to delete
        """
        try:
            self.client.remove_object(MINIO_BUCKET, object_name)
            logger.info(f"Deleted audio from MinIO: {object_name}")

        except S3Error as e:
            logger.error(f"Failed to delete audio from MinIO: {e}")
            raise

    def get_presigned_url(self, object_name: str, expires: timedelta = timedelta(hours=1)) -> str:
        """
        Get presigned URL for direct audio download (optional, for future use)

        Args:
            object_name: Object name
            expires: URL expiration time

        Returns:
            str: Presigned URL
        """
        try:
            url = self.client.presigned_get_object(
                bucket_name=MINIO_BUCKET,
                object_name=object_name,
                expires=expires
            )
            logger.info(f"Generated presigned URL for: {object_name}")
            return url

        except S3Error as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise

    def object_exists(self, object_name: str) -> bool:
        """
        Check if object exists in MinIO

        Args:
            object_name: Object name to check

        Returns:
            bool: True if exists, False otherwise
        """
        try:
            self.client.stat_object(MINIO_BUCKET, object_name)
            return True
        except S3Error:
            return False


# Singleton instance
_minio_service: Optional[MinIOService] = None


def get_minio_service() -> MinIOService:
    """Get or create MinIO service singleton"""
    global _minio_service
    if _minio_service is None:
        _minio_service = MinIOService()
    return _minio_service


def generate_object_name(user_id: int, transcription_id: int, filename: str) -> str:
    """
    Generate unique object name for audio file

    Args:
        user_id: User ID
        transcription_id: Transcription ID
        filename: Original filename

    Returns:
        str: Object name path (e.g., "audio/user_1/transcription_123_recording.webm")
    """
    # Sanitize filename - keep extension
    safe_filename = filename.replace("/", "_").replace("\\", "_")
    return f"audio/user_{user_id}/transcription_{transcription_id}_{safe_filename}"
