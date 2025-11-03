"""
SQLModel database models for EchoNote application.

This module defines the database schema for storing voice transcriptions
with their associated audio files.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class Priority(str, Enum):
    """Priority levels for voice notes"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Transcription(SQLModel, table=True):
    """
    Database model for storing voice transcriptions.

    Stores the transcribed text, audio file as binary data,
    and metadata about the recording.
    """
    __tablename__ = "transcriptions"

    id: Optional[int] = Field(default=None, primary_key=True)
    text: str = Field(index=True, description="Transcribed text from audio")
    audio_data: bytes = Field(description="Binary audio file data")
    audio_filename: str = Field(description="Original filename of the audio")
    audio_content_type: str = Field(
        default="audio/wav",
        description="MIME type of the audio file"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when transcription was created"
    )
    duration_seconds: Optional[float] = Field(
        default=None,
        description="Duration of audio in seconds"
    )
    priority: str = Field(
        default=Priority.MEDIUM.value,
        description="Priority level of the voice note"
    )


class TranscriptionCreate(SQLModel):
    """Schema for creating a new transcription (no ID, auto-generated timestamp)"""
    text: str
    audio_data: bytes
    audio_filename: str
    audio_content_type: str = "audio/wav"
    duration_seconds: Optional[float] = None
    priority: str = Priority.MEDIUM.value


class TranscriptionPublic(SQLModel):
    """Public schema for transcription (without binary audio data)"""
    id: int
    text: str
    audio_filename: str
    audio_content_type: str
    created_at: datetime
    duration_seconds: Optional[float]
    priority: str


class TranscriptionList(SQLModel):
    """Schema for listing transcriptions with pagination"""
    transcriptions: list[TranscriptionPublic]
    total: int
    skip: int
    limit: int
