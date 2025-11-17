"""
SQLModel database models for EchoNote application.

This module defines the database schema for storing voice transcriptions
with their associated audio files and user authentication.
"""

from datetime import datetime, date
from enum import Enum
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class Priority(str, Enum):
    """Priority levels for voice notes"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ============================================================================
# User Models
# ============================================================================

class User(SQLModel, table=True):
    """
    Database model for user accounts.

    Stores user credentials and metadata for authentication.
    """
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, min_length=3, max_length=50)
    email: str = Field(index=True, unique=True)
    hashed_password: str = Field(description="Bcrypt hashed password")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when user was created"
    )
    is_active: bool = Field(default=True, description="Whether user account is active")

    # Role-Based Access Control
    role: str = Field(default="user", max_length=20, index=True, description="User role (user, admin)")

    # Premium Features
    is_premium: bool = Field(default=False, description="Whether user has premium status")

    # Quota Management
    ai_action_quota_daily: int = Field(default=100, description="Daily AI action quota limit")
    ai_action_count_today: int = Field(default=0, description="AI actions used today")
    quota_reset_date: date = Field(
        default_factory=lambda: datetime.utcnow().date(),
        description="Date when quota was last reset"
    )

    # Updated timestamp
    updated_at: Optional[datetime] = Field(default=None, description="Timestamp when user was last updated")

    # Relationship to transcriptions
    transcriptions: list["Transcription"] = Relationship(back_populates="user")


class UserCreate(SQLModel):
    """Schema for user registration"""
    username: str = Field(min_length=3, max_length=50)
    email: str
    password: str = Field(min_length=8, max_length=100)


class UserPublic(SQLModel):
    """Public schema for user (without password)"""
    id: int
    username: str
    email: str
    created_at: datetime
    is_active: bool
    role: str
    is_premium: bool
    ai_action_quota_daily: int
    ai_action_count_today: int
    quota_reset_date: date


class UserLogin(SQLModel):
    """Schema for user login"""
    username: str
    password: str


class Token(SQLModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(SQLModel):
    """Schema for JWT token payload"""
    username: Optional[str] = None


# ============================================================================
# Transcription Models
# ============================================================================

class Transcription(SQLModel, table=True):
    """
    Database model for storing voice transcriptions.

    Stores the transcribed text, audio file as binary data,
    and metadata about the recording. Each transcription belongs to a user.
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
    url: Optional[str] = Field(
        default=None,
        description="Optional URL associated with the voice note"
    )

    # Background task tracking fields
    task_id: Optional[str] = Field(
        default=None,
        index=True,
        description="Celery task ID for tracking background processing"
    )
    status: str = Field(
        default="completed",
        description="Processing status: pending, processing, completed, failed"
    )
    progress: Optional[int] = Field(
        default=None,
        description="Processing progress percentage (0-100)"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if transcription failed"
    )

    # Foreign key to user
    user_id: int = Field(foreign_key="users.id", index=True)

    # Relationship to user
    user: Optional[User] = Relationship(back_populates="transcriptions")


class TranscriptionCreate(SQLModel):
    """Schema for creating a new transcription (no ID, auto-generated timestamp)"""
    text: str
    audio_data: bytes
    audio_filename: str
    audio_content_type: str = "audio/wav"
    duration_seconds: Optional[float] = None
    priority: str = Priority.MEDIUM.value
    url: Optional[str] = None


class TranscriptionPublic(SQLModel):
    """Public schema for transcription (without binary audio data)"""
    id: int
    text: str
    audio_filename: str
    audio_content_type: str
    created_at: datetime
    duration_seconds: Optional[float]
    priority: str
    url: Optional[str]
    task_id: Optional[str] = None
    status: str = "completed"
    progress: Optional[int] = None
    error_message: Optional[str] = None


class TranscriptionUpdate(SQLModel):
    """Schema for updating a transcription (e.g., priority)"""
    priority: Optional[str] = None


class TranscriptionList(SQLModel):
    """Schema for listing transcriptions with pagination"""
    transcriptions: list[TranscriptionPublic]
    total: int
    skip: int
    limit: int


class TranscriptionStatusResponse(SQLModel):
    """Schema for transcription status endpoint response"""
    id: int
    status: str
    progress: Optional[int]
    task_id: Optional[str]
    error_message: Optional[str]


class BulkStatusResponse(SQLModel):
    """Schema for bulk status endpoint response"""
    statuses: list[TranscriptionStatusResponse]
