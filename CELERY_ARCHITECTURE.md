# Celery Architecture - Proper Beat/Worker Separation

**Last Updated:** 2025-11-17

## Overview

This document explains the **proper** Celery architecture for separating Beat scheduler from Workers, following official Celery best practices for minimal dependencies.

---

## Architecture Components

### 1. Celery App Configuration (`backend/celery_app.py`)
- **Purpose**: Defines Celery application configuration
- **Key Feature**: Does NOT import tasks at module level
- **Beat Schedule**: Uses **string task names** (e.g., `'reset_daily_quotas'`)
- **Why**: Keeps configuration lightweight - Beat only needs task names, not implementations

```python
beat_schedule={
    'reset-daily-quotas': {
        'task': 'reset_daily_quotas',  # String name, not Python import!
        'schedule': crontab(hour=0, minute=0),
    },
}
```

### 2. Beat Scheduler Container (`echonote-celery-beat`)
- **Purpose**: Sends scheduled tasks to Redis queue at specified times
- **Dependencies**: Minimal (`requirements-beat.txt`)
  - ✅ Celery, Redis client
  - ✅ FastAPI, SQLModel (for config/models)
  - ❌ No audio processing (pydub, soundfile, librosa)
  - ❌ No ML libraries (PyTorch, pyannote.audio)
  - ❌ No API clients (openai)
- **How it works**:
  - Reads `beat_schedule` from celery_app config
  - At scheduled times, sends task NAME (string) to Redis
  - Does NOT execute tasks - just schedules them
- **Image size**: ~400MB (vs worker's ~2GB+)

### 3. Worker Container (`echonote-celery-worker`)
- **Purpose**: Executes tasks from Redis queue
- **Dependencies**: Full (`requirements.txt`)
  - ✅ All audio processing libraries
  - ✅ ML/AI libraries for transcription & diarization
  - ✅ All task execution dependencies
- **How it works**:
  - Uses `--include=backend.tasks` flag to import task modules
  - Registers task functions with Celery
  - Picks up tasks from Redis queue by name
  - Executes the actual Python functions
- **Image size**: ~2GB+ (includes PyTorch, ffmpeg, etc.)

---

## Why This Architecture?

### The Problem (Original Approach)
```python
# ❌ BAD: celery_app.py importing tasks at module level
from backend import tasks  # This forces BOTH beat and worker to have all dependencies
```

**Issues**:
- Beat container needed all audio/ML libraries just to import config
- Defeats the purpose of separation
- Huge container sizes for a simple scheduler

### The Solution (Proper Approach)

**1. celery_app.py: No task imports**
```python
# ✅ GOOD: Only configuration, no imports
beat_schedule = {
    'reset-daily-quotas': {
        'task': 'reset_daily_quotas',  # String, not import!
        'schedule': crontab(hour=0, minute=0),
    },
}
```

**2. Worker: Import tasks via CLI flag**
```bash
celery -A backend.celery_app worker --include=backend.tasks
```

**3. Beat: No task imports needed**
```bash
celery -A backend.celery_app beat  # Just reads beat_schedule strings
```

---

## How Task Execution Works

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Beat Scheduler (echonote-celery-beat)                       │
│    - Reads beat_schedule configuration                          │
│    - At midnight UTC: Sends message to Redis                    │
│      Message: "Execute task named 'reset_daily_quotas'"         │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Redis Queue                                                  │
│    - Stores: {"task": "reset_daily_quotas", "args": [], ...}    │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Worker (echonote-celery-worker)                             │
│    - Picks up message from Redis                                │
│    - Looks up 'reset_daily_quotas' in task registry            │
│    - Finds: reset_daily_quotas_task() from backend.tasks       │
│    - Executes the actual Python function                        │
│    - Updates database with results                              │
└─────────────────────────────────────────────────────────────────┘
```

**Key Point**: Beat never executes code - it just knows task **names**. Workers execute the actual **code**.

---

## Files Structure

```
backend/
├── celery_app.py              # Celery config (NO task imports)
├── tasks.py                   # Task definitions (@celery_app.task decorators)
├── requirements.txt           # Full dependencies (for workers)
├── requirements-beat.txt      # Minimal dependencies (for beat)
├── Containerfile.celery       # Worker: --include=backend.tasks
└── Containerfile.celery-beat  # Beat: no include needed
```

---

## Benefits of This Approach

✅ **Minimal Dependencies**: Beat container is 5x smaller
✅ **Faster Builds**: Beat rebuilds quickly (no PyTorch compilation)
✅ **Clear Separation**: Beat = scheduler, Worker = executor
✅ **Official Pattern**: Follows Celery documentation best practices
✅ **Scalability**: Can scale workers independently

---

## Key Celery Concepts

### Task Names vs Task Objects

**Task Name (String)**:
```python
'task': 'reset_daily_quotas'  # Just a string identifier
```

**Task Object (Python function)**:
```python
@celery_app.task(name="reset_daily_quotas")
def reset_daily_quotas_task():
    # Actual implementation
    pass
```

**Beat uses**: Task names (strings)
**Workers use**: Task objects (Python functions)

### Task Discovery

**Workers** discover tasks via:
1. `--include` flag: `--include=backend.tasks`
2. `conf.imports` setting: `celery_app.conf.imports = ('backend.tasks',)`
3. `autodiscover_tasks()`: For Django/Flask auto-discovery

**Beat** doesn't discover - it just uses the names from `beat_schedule`.

---

## Common Pitfalls

### ❌ Importing tasks in celery_app.py
```python
# DON'T DO THIS
from backend import tasks  # Forces beat to have all dependencies
```

### ❌ Using task objects in beat_schedule
```python
# DON'T DO THIS
from backend.tasks import my_task
beat_schedule = {
    'run-task': {
        'task': my_task,  # This is a Python object, requires import!
    }
}
```

### ✅ Using string names in beat_schedule
```python
# DO THIS
beat_schedule = {
    'run-task': {
        'task': 'backend.tasks.my_task',  # String name, no import needed!
    }
}
```

---

## Testing the Setup

### Verify Beat is Running
```bash
podman logs echonote-celery-beat 2>&1 | grep "beat: Starting"
# Should show: [INFO/MainProcess] beat: Starting...
```

### Verify Worker Registered Tasks
```bash
podman logs echonote-celery-worker 2>&1 | grep "registered\|tasks"
# Should show: [tasks] . backend.tasks.reset_daily_quotas_task
```

### Check Schedule
```bash
podman exec echonote-celery-beat celery -A backend.celery_app inspect scheduled
# Should show scheduled tasks (may be empty if none pending)
```

### Trigger Manual Test (from worker container)
```bash
podman exec echonote-celery-worker celery -A backend.celery_app call reset_daily_quotas
```

---

## References

- [Celery Periodic Tasks Documentation](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html)
- [Celery Beat Architecture](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html#starting-the-scheduler)
- [Task Naming](https://docs.celeryq.dev/en/stable/userguide/tasks.html#names)
- [Calling Tasks](https://docs.celeryq.dev/en/stable/userguide/calling.html)

---

## Conclusion

This architecture follows **official Celery best practices**:
- Beat is a lightweight scheduler with minimal dependencies
- Workers are heavy executors with full task code
- Task references use strings, not Python imports
- Clean separation enables independent scaling and smaller images

**This is NOT a hack** - it's the proper way to deploy Celery in production! 🚀
