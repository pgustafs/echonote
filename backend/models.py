"""
SQLModel database models for EchoNote application.

This module defines the database schema for storing voice transcriptions
with their associated audio files and user authentication.
"""

from datetime import datetime, date
from enum import Enum
from typing import Optional
import uuid
import re

from sqlmodel import Field, Relationship, SQLModel, Column, Text
from sqlalchemy import Column as SAColumn, Text as SAText
from pydantic import validator


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
    """
    Schema for user registration with enhanced validation.

    Phase 4: Security Hardening - Password complexity and input validation
    """
    username: str = Field(min_length=3, max_length=50)
    email: str
    password: str = Field(min_length=8, max_length=100)

    @validator('password')
    def validate_password_strength(cls, v):
        """
        Validate password complexity requirements.

        Requirements:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit

        Raises:
            ValueError: If password doesn't meet complexity requirements
        """
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        return v

    @validator('email')
    def validate_email_format(cls, v):
        """
        Validate email format using regex.

        Ensures email follows standard format: user@domain.tld

        Raises:
            ValueError: If email format is invalid
        """
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, v):
            raise ValueError('Invalid email format')
        return v.lower()

    @validator('username')
    def validate_username_format(cls, v):
        """
        Validate username contains only allowed characters.

        Allowed: letters, numbers, hyphens, and underscores

        Raises:
            ValueError: If username contains invalid characters
        """
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v


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
    """
    Schema for JWT token response.

    Phase 4.1: Security fix - Added refresh_token support
    """
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None  # Phase 4.1: Optional refresh token for extended sessions


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

    # Audio storage - Legacy BLOB field (deprecated, use minio_object_path instead)
    audio_data: Optional[bytes] = Field(default=None, description="Binary audio file data (deprecated)")

    # MinIO object storage path
    minio_object_path: Optional[str] = Field(
        default=None,
        description="Path to audio file in MinIO object storage (e.g., 'audio/user_1/transcription_123.webm')"
    )

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


# ============================================================================
# AI Action Models
# ============================================================================

class AIAction(SQLModel, table=True):
    """
    Database model for tracking AI actions performed on transcriptions.

    Stores request parameters, results, and metadata for AI-powered operations
    like summarization, translation, content generation, etc.
    """
    __tablename__ = "ai_actions"

    # Primary Key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Unique Action ID (UUID v4 for API responses)
    action_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        index=True,
        unique=True,
        description="Unique identifier for this action"
    )

    # Foreign Keys
    user_id: int = Field(foreign_key="users.id", index=True, description="User who requested this action")
    transcription_id: Optional[int] = Field(
        default=None,
        foreign_key="transcriptions.id",
        index=True,
        nullable=True,
        description="Transcription this action operates on (optional for chat and improve actions)"
    )

    # Action Details
    action_type: str = Field(
        max_length=100,
        index=True,
        description="Type of AI action (e.g., 'analyze', 'create/linkedin-post')"
    )
    status: str = Field(
        default="work_in_progress",
        max_length=20,
        index=True,
        description="Status: pending, processing, completed, failed, work_in_progress"
    )

    # Request/Response Data (JSON stored as text)
    request_params: str = Field(
        default="{}",
        sa_column=SAColumn(SAText),
        description="JSON string of request parameters"
    )
    result_data: Optional[str] = Field(
        default=None,
        sa_column=SAColumn(SAText, nullable=True),
        description="JSON string of result data"
    )
    error_message: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Error message if action failed"
    )

    # Quota Tracking
    quota_cost: int = Field(default=1, description="Quota cost for this action")

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the action was created"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When the action was completed"
    )

    # Performance Metrics
    processing_duration_ms: Optional[int] = Field(
        default=None,
        description="Processing duration in milliseconds"
    )


class AIActionRequest(SQLModel):
    """Base schema for AI action requests"""
    transcription_id: int = Field(gt=0, description="ID of the transcription to process")
    options: dict = Field(default_factory=dict, description="Action-specific options")


class ImproveActionRequest(SQLModel):
    """Request to improve a previous AI action result with additional instructions"""
    session_id: str = Field(description="LlamaStack session ID from the original action")
    instructions: str = Field(min_length=1, description="How to improve the result (e.g., 'make it shorter')")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc-123-def-456",
                "instructions": "Make it shorter and more professional"
            }
        }


class ChatRequest(SQLModel):
    """Request for chat with AI model"""
    message: str = Field(min_length=1, description="Your message to the AI")
    session_id: Optional[str] = Field(default=None, description="Continue existing conversation (optional)")
    transcription_id: Optional[int] = Field(default=None, gt=0, description="Chat about specific transcription (optional)")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Can you help me write a professional email?",
                "session_id": None,
                "transcription_id": None
            }
        }


class AIActionResponse(SQLModel):
    """Base schema for AI action responses"""
    action_id: str = Field(description="Unique identifier for this action")
    status: str = Field(description="Current status of the action")
    message: str = Field(description="Human-readable message about the action")
    quota_remaining: int = Field(description="User's remaining quota after this action")
    quota_reset_date: str = Field(description="Date when quota will reset")
    result: Optional[dict] = Field(default=None, description="Action result data")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    created_at: datetime = Field(description="When the action was created")
    completed_at: Optional[datetime] = Field(default=None, description="When the action was completed")
    session_id: Optional[str] = Field(default=None, description="LlamaStack session ID for conversation continuity")


class AIActionPublic(SQLModel):
    """Public schema for listing AI actions (without full request/response data)"""
    id: int
    action_id: str
    action_type: str
    status: str
    quota_cost: int
    created_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]


class AIActionList(SQLModel):
    """Schema for listing AI actions with pagination"""
    actions: list[AIActionPublic]
    total: int
    skip: int
    limit: int
