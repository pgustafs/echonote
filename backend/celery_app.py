"""
Celery application for EchoNote background task processing.

This module configures Celery for distributed transcription processing
with Redis as the message broker and result backend.

Architecture:
    - Broker: Redis database 0 (task queue)
    - Backend: Redis database 1 (task results)
    - Workers: Process transcription tasks with automatic chunking
    - Serialization: JSON for cross-platform compatibility

Usage:
    # Start worker
    celery -A backend.celery_app worker --loglevel=info

    # Monitor tasks
    celery -A backend.celery_app flower
"""

import logging
from celery import Celery
from celery.schedules import crontab
from backend.config import settings

logger = logging.getLogger(__name__)

# Create Celery application instance
celery_app = Celery('echonote')

# Configure Celery
celery_app.conf.update(
    # Broker and backend
    broker_url=settings.CELERY_BROKER_URL,
    result_backend=settings.CELERY_RESULT_BACKEND,

    # Serialization (use JSON for security and compatibility)
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],

    # Timezone
    timezone='UTC',
    enable_utc=True,

    # Task tracking
    task_track_started=True,  # Track when tasks actually start processing
    task_send_sent_event=True,  # Send task-sent events

    # Task time limits (prevent hung tasks)
    task_time_limit=3600,  # Hard limit: 1 hour
    task_soft_time_limit=3300,  # Soft limit: 55 minutes (raises exception)

    # Result expiration
    result_expires=86400,  # Results expire after 24 hours

    # Task acknowledgment
    task_acks_late=True,  # Acknowledge task after completion (enables retry on worker crash)
    task_reject_on_worker_lost=True,  # Reject task if worker dies unexpectedly

    # Retry settings
    task_publish_retry=True,  # Retry publishing if broker connection lost
    task_publish_retry_policy={
        'max_retries': 3,
        'interval_start': 0,
        'interval_step': 0.2,
        'interval_max': 0.5,
    },

    # Worker settings
    worker_prefetch_multiplier=1,  # Only fetch 1 task at a time (good for long-running tasks)
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks (prevent memory leaks)

    # Event settings (for monitoring with Flower)
    worker_send_task_events=True,

    # Beat schedule (for periodic tasks)
    beat_schedule={
        'reset-daily-quotas': {
            'task': 'reset_daily_quotas',
            'schedule': crontab(hour=0, minute=0),  # Every day at midnight UTC
        },
    },
)

# Task discovery configuration
# IMPORTANT: We do NOT import tasks here to keep celery_app.py lightweight
# - Beat scheduler: Only needs task names as strings in beat_schedule (no imports needed)
# - Workers: Will import tasks using --include flag at startup (see Containerfile.celery CMD)
# This allows Beat container to have minimal dependencies (no audio/ML packages)

# Task routes (optional: route specific tasks to specific queues)
# celery_app.conf.task_routes = {
#     'backend.tasks.transcribe_audio_task': {'queue': 'transcription'},
#     'backend.tasks.high_priority_task': {'queue': 'high_priority'},
# }

if __name__ == '__main__':
    celery_app.start()
