# User Roles and Quotas System

**Last Updated:** 2025-11-17

## Overview

EchoNote implements a comprehensive **Role-Based Access Control (RBAC)** and **Daily Quota System** to manage user permissions and AI resource usage in multi-user environments. This system ensures fair resource allocation while providing administrative capabilities for privileged users.

---

## Role-Based Access Control (RBAC)

### User Roles

EchoNote supports two primary user roles:

#### 1. Standard User (`role: "user"`)
- **Default role** assigned to all new registrations
- Subject to daily AI action quotas
- Can perform all standard operations within quota limits
- Cannot modify other users' data
- Cannot adjust quotas or roles

#### 2. Administrator (`role: "admin"`)
- **Unlimited access** to all AI actions (bypasses quota checks)
- Can manage users, quotas, and system settings
- Access to admin-only endpoints
- Can view usage statistics for all users
- Can manually adjust user quotas and roles

### Role Assignment

**Default Assignment:**
- All new user registrations receive `role: "user"`
- Default quota: 100 AI actions per day

**Changing Roles:**
Currently, role changes must be performed directly in the database. Future versions will include admin UI for role management.

```sql
-- Promote user to admin (direct database update)
UPDATE users SET role = 'admin' WHERE username = 'alice';

-- Demote admin to user
UPDATE users SET role = 'user' WHERE username = 'bob';
```

---

## Daily Quota System

### Quota Configuration

Each user has the following quota-related fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `ai_action_quota_daily` | Integer | 100 | Maximum AI actions allowed per day |
| `ai_action_count_today` | Integer | 0 | Current count of AI actions used today |
| `quota_reset_date` | Date | Today | Date when quota was last reset |
| `is_premium` | Boolean | False | Premium user flag (higher quotas) |

### Quota Costs

Different AI actions have different quota costs:

| Action Type | Cost | Example |
|-------------|------|---------|
| Transcription | 1 | Standard audio transcription |
| AI Summary | 2 | Generate summary from transcription |
| AI Action (Future) | Variable | Complex AI operations |

**Note:** Quota costs are configurable via the `PermissionService.get_quota_cost()` method.

### Premium Users

Premium users (`is_premium: True`) receive higher daily quotas:

- **Standard User**: 100 AI actions/day
- **Premium User**: 500 AI actions/day (configurable)
- **Admin**: Unlimited (bypasses all checks)

---

## Automatic Quota Reset

Quotas are automatically reset daily at **midnight UTC** via the Celery Beat scheduler.

### Reset Mechanism

**Celery Beat Scheduler** (`echonote-celery-beat` container):
- Runs scheduled task: `reset_daily_quotas`
- Schedule: Every day at 00:00 UTC (cron: `0 0 * * *`)
- Task defined in: `backend/tasks.py`
- Configuration: `backend/celery_app.py` beat_schedule

**Reset Process:**
```python
# Executed at midnight UTC
def reset_daily_quotas_task():
    # For all users where quota_reset_date < today:
    1. Set ai_action_count_today = 0
    2. Set quota_reset_date = today
    3. Log reset event
```

**Monitoring Reset:**
```bash
# Check beat scheduler logs
podman logs echonote-celery-beat 2>&1 | grep "reset-daily-quotas"

# Check worker logs for task execution
podman logs echonote-celery-worker 2>&1 | grep "Daily quota reset"

# Manually trigger reset for testing (runs immediately)
podman exec echonote-celery-worker celery -A backend.celery_app call reset_daily_quotas
```

---

## Quota Enforcement

### Enforcement Decorators

EchoNote provides decorators for easy quota enforcement on API endpoints:

#### `@require_quota(cost=1)`
Checks if user has sufficient quota before processing request.

```python
from backend.middleware.quota_checker import require_quota

@router.post("/api/transcribe")
@require_quota(cost=1)
async def transcribe_audio(
    file: UploadFile,
    current_user: User = Depends(get_current_active_user)
):
    # This endpoint will only execute if user has >= 1 quota remaining
    # Admin users bypass this check automatically
    pass
```

#### `@require_role(role)`
Restricts endpoint access to specific roles.

```python
from backend.middleware.quota_checker import require_role

@router.get("/api/admin/users")
@require_role("admin")
async def list_all_users(current_user: User = Depends(get_current_active_user)):
    # Only admin users can access this endpoint
    # Returns 403 Forbidden for non-admin users
    pass
```

#### `@track_usage(action_type)`
Tracks and increments usage after successful operation.

```python
from backend.middleware.quota_checker import track_usage

@router.post("/api/summarize")
@require_quota(cost=2)
@track_usage(action_type="summary")
async def generate_summary(
    transcription_id: int,
    current_user: User = Depends(get_current_active_user)
):
    # Quota checked before execution
    # Usage incremented by 2 after successful completion
    pass
```

### Enforcement Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. User sends API request                                       │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Authentication Middleware                                    │
│    - Validate JWT token                                         │
│    - Load user from database                                    │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. @require_quota Decorator                                     │
│    - Check if user.role == "admin" → ALLOW (bypass)            │
│    - Check if quota_reset_date < today → Auto-reset            │
│    - Check: (quota_daily - count_today) >= cost → ALLOW/DENY   │
└─────────────────────────────────────────────────────────────────┘
                            │
                    ┌───────┴───────┐
                    │               │
                ALLOW             DENY
                    │               │
                    ▼               ▼
        ┌───────────────┐  ┌──────────────────┐
        │ Execute       │  │ Return 429       │
        │ endpoint      │  │ "Quota exceeded" │
        └───────────────┘  └──────────────────┘
                    │
                    ▼
        ┌───────────────────────────┐
        │ @track_usage Decorator    │
        │ - Increment count_today   │
        │ - Log usage event         │
        └───────────────────────────┘
```

---

## Quota Management API

### Permission Service

The `PermissionService` class provides quota management methods:

**Location:** `backend/services/permission_service.py`

#### Key Methods

**`check_user_quota(user: User, quota_cost: int = 1) -> bool`**
- Checks if user has sufficient quota
- Auto-resets quota if date changed
- Admins always return `True`

```python
from backend.services.permission_service import PermissionService

if PermissionService.check_user_quota(user, cost=2):
    # User has enough quota
    pass
else:
    # Quota exceeded
    raise HTTPException(status_code=429, detail="Daily quota exceeded")
```

**`increment_usage(session: Session, user_id: int, quota_cost: int = 1) -> User`**
- Increments user's daily quota usage
- Updates database
- Returns updated user object

```python
updated_user = PermissionService.increment_usage(session, user.id, cost=2)
# user.ai_action_count_today increased by 2
```

**`reset_daily_quotas(session: Session) -> int`**
- Resets all users' quotas to 0
- Updates quota_reset_date to today
- Returns count of users reset

```python
count = PermissionService.reset_daily_quotas(session)
# Returns: 42 (users reset)
```

**`get_user_usage_stats(user: User) -> dict`**
- Returns detailed usage statistics
- Includes quota remaining, percentage used, reset date

```python
stats = PermissionService.get_user_usage_stats(user)
# {
#     "quota_daily": 100,
#     "count_today": 23,
#     "remaining": 77,
#     "percentage_used": 23.0,
#     "quota_reset_date": "2025-11-18",
#     "is_premium": False,
#     "role": "user"
# }
```

**`check_role_permission(user: User, required_role: str) -> bool`**
- Checks if user has required role
- Admins always have all permissions

```python
if PermissionService.check_role_permission(user, "admin"):
    # User is admin
    pass
```

**`get_quota_cost(action_type: str) -> int`**
- Returns quota cost for action type
- Configurable mapping

```python
cost = PermissionService.get_quota_cost("transcription")  # Returns: 1
cost = PermissionService.get_quota_cost("summary")        # Returns: 2
```

---

## User Information API

### Get Current User Quota Status

**Endpoint:** `GET /api/auth/me`

**Headers:** `Authorization: Bearer <jwt_token>`

**Response:**
```json
{
  "id": 42,
  "username": "alice",
  "email": "alice@example.com",
  "created_at": "2025-11-01T10:00:00Z",
  "is_active": true,
  "role": "user",
  "is_premium": false,
  "ai_action_quota_daily": 100,
  "ai_action_count_today": 23,
  "quota_reset_date": "2025-11-18"
}
```

**Usage Example:**
```typescript
// Frontend: Display quota status
const response = await fetch('/api/auth/me', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const user = await response.json();

// Show user: "23/100 AI actions used today (77 remaining)"
const remaining = user.ai_action_quota_daily - user.ai_action_count_today;
console.log(`${user.ai_action_count_today}/${user.ai_action_quota_daily} used (${remaining} remaining)`);
```

---

## Database Schema

### Users Table

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,

    -- Role and permissions
    role VARCHAR(20) DEFAULT 'user' NOT NULL,
    is_premium BOOLEAN DEFAULT FALSE,

    -- Quota management
    ai_action_quota_daily INTEGER DEFAULT 100,
    ai_action_count_today INTEGER DEFAULT 0,
    quota_reset_date DATE DEFAULT CURRENT_DATE
);

-- Indexes for performance
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_quota_reset_date ON users(quota_reset_date);
```

### Migration History

Quota and permission fields were added in migration:
- **File:** `backend/alembic/versions/003_add_user_quotas_and_permissions.py`
- **Applied:** 2025-11-17
- **Changes:**
  - Added `role` field (default: "user")
  - Added `is_premium` field (default: False)
  - Added `ai_action_quota_daily` field (default: 100)
  - Added `ai_action_count_today` field (default: 0)
  - Added `quota_reset_date` field (nullable for SQLite compatibility)
  - Added `updated_at` field (nullable)

**Apply Migration:**
```bash
# Run migration
podman exec echonote-backend alembic upgrade head

# Or for development:
alembic upgrade head
```

---

## Admin Capabilities

### Current Admin Features

**1. Unlimited AI Actions**
- Admins bypass all quota checks
- No daily limits on transcriptions or AI operations

**2. Role-Based Endpoint Access**
- Admin-only endpoints protected by `@require_role("admin")`
- Examples: user management, system statistics

**3. Usage Visibility**
- Can view usage statistics for all users
- Can monitor quota consumption patterns

### Future Admin Features (Planned)

- **User Management UI**: Create, modify, delete users
- **Quota Adjustment**: Manually set user quotas
- **Role Management**: Promote/demote users via UI
- **Usage Analytics**: Dashboard with usage trends
- **Audit Logs**: View all user actions and quota events
- **Bulk Operations**: Reset quotas, send notifications

---

## Security Considerations

### JWT Authentication

All quota-related operations require valid JWT authentication:

**Token Format:**
```json
{
  "sub": "alice",  // Username
  "exp": 1700000000  // Expiration timestamp
}
```

**Validation:**
- Token must be valid and not expired
- User must exist in database
- User must be active (`is_active: True`)

### Audit Logging

All quota-related events are logged to `backend/logs/security.log`:

**Logged Events:**
- User registration (with initial quota)
- Login attempts (failed and successful)
- Quota exceeded attempts (429 responses)
- Admin actions (role changes, quota adjustments)
- Scheduled quota resets

**Example Log Entry:**
```json
{
  "timestamp": "2025-11-17T14:30:45.123Z",
  "level": "WARNING",
  "event_type": "quota_exceeded",
  "user_id": 42,
  "username": "alice",
  "action_type": "transcription",
  "quota_cost": 1,
  "quota_remaining": 0,
  "ip_address": "192.168.1.100"
}
```

---

## Usage Examples

### Example 1: Standard User Workflow

```python
# 1. User registers (automatic quota assignment)
POST /api/auth/register
{
  "username": "alice",
  "email": "alice@example.com",
  "password": "secure123"
}

# Response: User created with:
# - role: "user"
# - ai_action_quota_daily: 100
# - ai_action_count_today: 0

# 2. User performs transcription (cost: 1)
POST /api/transcribe
Headers: Authorization: Bearer <token>
Body: { file: audio.wav }

# Quota check:
# - ai_action_count_today: 0 < 100 ✓ ALLOWED
# - After completion: ai_action_count_today = 1

# 3. User checks quota status
GET /api/auth/me

# Response:
# {
#   "ai_action_quota_daily": 100,
#   "ai_action_count_today": 1,
#   "quota_reset_date": "2025-11-18"
# }

# 4. User exceeds quota (after 99 more actions)
POST /api/transcribe
Headers: Authorization: Bearer <token>

# Quota check:
# - ai_action_count_today: 100 >= 100 ✗ DENIED
# - Response: 429 Too Many Requests
# {
#   "detail": "Daily quota exceeded. Resets at midnight UTC."
# }

# 5. Next day (automatic reset at 00:00 UTC)
# Celery Beat executes reset_daily_quotas_task:
# - ai_action_count_today: 100 → 0
# - quota_reset_date: "2025-11-17" → "2025-11-18"

# 6. User can perform actions again
POST /api/transcribe
# ✓ ALLOWED (quota reset)
```

### Example 2: Admin User Workflow

```python
# 1. Admin user logs in
POST /api/auth/login
{
  "username": "admin",
  "password": "adminpass"
}

# User has:
# - role: "admin"
# - Bypasses all quota checks

# 2. Admin performs 500 transcriptions in one day
for i in range(500):
    POST /api/transcribe
    # All ALLOWED (admin bypass)

# 3. Admin accesses admin-only endpoint
GET /api/admin/users
# ✓ ALLOWED (role check passed)

# 4. Standard user tries same endpoint
GET /api/admin/users
# ✗ DENIED (403 Forbidden - insufficient role)
```

### Example 3: Premium User Workflow

```python
# 1. Upgrade user to premium (database update)
UPDATE users SET is_premium = True, ai_action_quota_daily = 500
WHERE username = 'alice';

# 2. User now has higher quota
GET /api/auth/me

# Response:
# {
#   "is_premium": true,
#   "ai_action_quota_daily": 500,
#   "ai_action_count_today": 0
# }

# 3. User can perform 500 actions per day
# (5x standard user quota)
```

---

## Implementation Details

### File Structure

```
backend/
├── services/
│   └── permission_service.py       # Quota management logic
├── middleware/
│   ├── audit_logger.py             # Request logging
│   └── quota_checker.py            # Quota decorators
├── models.py                       # User model with quota fields
├── auth_routes.py                  # User registration/login
├── tasks.py                        # Celery task: reset_daily_quotas
└── celery_app.py                   # Beat schedule configuration
```

### Key Components

**PermissionService** (`backend/services/permission_service.py`)
- Centralized quota logic
- No HTTP dependencies (pure business logic)
- Reusable across endpoints

**Quota Decorators** (`backend/middleware/quota_checker.py`)
- FastAPI dependency injection
- Automatic enforcement
- Error handling

**Audit Middleware** (`backend/middleware/audit_logger.py`)
- Logs all authenticated requests
- Sanitizes sensitive data
- Tracks quota events

**Celery Tasks** (`backend/tasks.py`)
- Scheduled quota reset at midnight UTC
- Runs via Celery Beat scheduler
- Idempotent (safe to run multiple times)

---

## Troubleshooting

### Quota Not Resetting

**Symptom:** Users report quotas not resetting at midnight UTC.

**Diagnosis:**
```bash
# 1. Check if Beat scheduler is running
podman logs echonote-celery-beat 2>&1 | grep "beat: Starting"
# Should see: [INFO/MainProcess] beat: Starting...

# 2. Check if reset task is scheduled
podman logs echonote-celery-beat 2>&1 | grep "reset-daily-quotas"
# Note: Schedule only visible at DEBUG level

# 3. Check worker logs for task execution
podman logs echonote-celery-worker 2>&1 | grep "Daily quota reset"
# Should see: Daily quota reset completed for X users

# 4. Manually trigger reset for testing
podman exec echonote-celery-worker celery -A backend.celery_app call reset_daily_quotas
```

**Fix:**
- Ensure `echonote-celery-beat` container is running
- Verify `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` are correct
- Check database connectivity from Beat container

### User Quota Not Updating

**Symptom:** User performs actions but `ai_action_count_today` doesn't increase.

**Diagnosis:**
```bash
# 1. Check backend logs for quota tracking
podman logs echonote-backend 2>&1 | grep "quota"

# 2. Verify @track_usage decorator is present on endpoint
# Check backend/routers/transcriptions.py

# 3. Check database directly
podman exec echonote-backend sqlite3 /opt/app-root/src/data/echonote.db \
  "SELECT username, ai_action_count_today, quota_reset_date FROM users WHERE username='alice';"
```

**Fix:**
- Ensure `@track_usage` decorator is applied to endpoints
- Verify decorator is AFTER `@require_quota` (order matters)
- Check for database connection errors in logs

### Admin Quota Bypass Not Working

**Symptom:** Admin user receives "Quota exceeded" errors.

**Diagnosis:**
```bash
# Check user role in database
podman exec echonote-backend sqlite3 /opt/app-root/src/data/echonote.db \
  "SELECT username, role FROM users WHERE username='admin';"

# Should return: admin|admin
```

**Fix:**
- Ensure `role` field is exactly "admin" (case-sensitive)
- Verify `PermissionService.check_user_quota()` checks admin role
- Re-login to get fresh JWT token with updated role

---

## Configuration

### Adjusting Default Quotas

Edit `backend/models.py`:

```python
class User(SQLModel, table=True):
    # Change default quota (affects new users only)
    ai_action_quota_daily: int = Field(default=200)  # Was 100
```

**Note:** Existing users retain their current quotas. To update existing users:

```sql
UPDATE users SET ai_action_quota_daily = 200 WHERE role = 'user';
```

### Changing Quota Costs

Edit `backend/services/permission_service.py`:

```python
@staticmethod
def get_quota_cost(action_type: str) -> int:
    costs = {
        "transcription": 1,      # Change as needed
        "summary": 3,            # Was 2
        "ai_action": 5,          # Custom action
    }
    return costs.get(action_type, 1)
```

### Modifying Reset Schedule

Edit `backend/celery_app.py`:

```python
beat_schedule = {
    'reset-daily-quotas': {
        'task': 'reset_daily_quotas',
        'schedule': crontab(hour=6, minute=0),  # 6 AM UTC instead of midnight
    },
}
```

---

## Best Practices

**1. Always Use Decorators**
- Use `@require_quota` on all AI-intensive endpoints
- Use `@track_usage` to increment counts
- Combine with `@require_role` for admin endpoints

**2. Provide User Feedback**
- Show quota status in UI (e.g., "23/100 actions used")
- Display quota reset time ("Resets at midnight UTC")
- Clear error messages when quota exceeded

**3. Monitor Quota Usage**
- Review `security.log` for quota exceeded events
- Identify users hitting limits frequently
- Adjust quotas or upgrade users to premium

**4. Test Quota Logic**
- Test quota enforcement with non-admin users
- Test admin bypass functionality
- Test automatic reset mechanism

**5. Database Performance**
- Index `quota_reset_date` for efficient reset queries
- Index `role` for permission checks
- Monitor query performance with many users

---

## References

- **Implementation Plan:** [AI_PLAN.md](AI_PLAN.md) - Full AI Actions roadmap
- **Celery Architecture:** [CELERY_ARCHITECTURE.md](CELERY_ARCHITECTURE.md) - Beat/Worker separation
- **Container Deployment:** [CONTAINER.md](CONTAINER.md) - Container setup guide
- **Main README:** [README.md](README.md) - General project documentation

---

## Future Enhancements

**Phase 2 - AI Actions API** (Planned):
- API endpoint: `POST /api/ai-actions` for AI-powered operations
- Quota enforcement on AI actions
- Detailed usage analytics per action type
- Per-action cost calculation

**Phase 3 - Admin UI** (Planned):
- Web-based admin dashboard
- User management interface
- Quota adjustment controls
- Usage analytics and reports
- Role management UI

**Phase 4 - Advanced Features** (Planned):
- Usage history and analytics
- Quota purchase/upgrade flow
- API rate limiting (requests per minute)
- Webhook notifications for quota events
- Customizable quota policies per user

---

## Support

For issues related to quotas or permissions:

1. Check logs: `podman logs echonote-backend 2>&1 | grep -i quota`
2. Review security logs: `backend/logs/security.log`
3. Verify Celery Beat is running: `podman logs echonote-celery-beat`
4. Test quota reset manually: `podman exec echonote-celery-worker celery -A backend.celery_app call reset_daily_quotas`

For questions or bug reports, open an issue on the project repository.
