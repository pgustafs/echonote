# EchoNote 🎤

A modern, beautiful voice transcription application built with FastAPI and Vite. Record voice messages, transcribe them using Whisper (via vLLM), and store both the audio and transcriptions in a database.

## Features

✨ **Modern UI** - Beautiful, responsive interface built with React and Tailwind CSS with streamlined single-button control
🔐 **User Authentication** - Secure JWT-based authentication with user registration and login
🛡️ **Security Hardening** - Production-ready security with rate limiting, password complexity, input sanitization, and brute force protection
🎙️ **Audio Recording** - Record directly in the browser with one-click start/stop using the microphone button
🤖 **AI Transcription** - Powered by Whisper (large-v3-turbo) via vLLM
⚡ **Background Processing** - Async transcription with Celery and Redis for responsive UX and progress tracking
🔄 **Real-time Updates** - Live status updates and progress bars without page refresh
👥 **Speaker Diarization** - Detect and separate different speakers using pyannote.audio (optional, CPU-only)
💾 **Persistent Storage** - Audio files and transcriptions stored in database with user ownership
🎵 **Audio Playback** - Listen to your recordings with built-in player
📥 **Download Package** - Download transcriptions as ZIP with WAV audio and config.json
🔍 **Search & Filter** - Full-text search in transcriptions with priority filtering
📱 **Responsive Design** - Works seamlessly on desktop and mobile with dedicated mobile layout
🌓 **Dark Mode Ready** - Beautiful UI in both light and dark themes
🎨 **Format Conversion** - Server-side WebM to WAV conversion with FFmpeg (isolated subprocess)
📴 **Progressive Web App** - Full PWA with offline recording, automatic sync, and installable app

## Progressive Web App Features

EchoNote is a **fully functional Progressive Web App** with comprehensive offline capabilities:

### Offline Capabilities

- **📴 Offline Recording** - Record voice messages even when offline
- **💾 Local Storage** - Recordings saved to IndexedDB until sync
- **🔄 Automatic Sync** - Auto-sync when connection is restored
- **📊 Sync Status** - Real-time sync indicator with pending count
- **🛡️ Blob Validation** - Three-layer corruption detection and prevention
- **🔁 Queue Management** - Sequential sync with error handling

### Installable App

- **📱 Add to Home Screen** - Install on mobile (iOS/Android)
- **🖥️ Desktop App** - Standalone window on desktop
- **🎨 Custom Icons** - Native app icons and splash screens
- **⚡ Instant Loading** - Cached app shell for instant start

### Smart Caching

- **🌐 Network-First Strategy** - Always try for latest data
- **💨 Cache Fallback** - Offline UI access when disconnected
- **🔄 Auto-Update** - Service worker updates every minute
- **📦 Strategic Caching** - Assets cached, API network-first

For complete PWA documentation, see **[PWA_IMPLEMENTATION.md](PWA_IMPLEMENTATION.md)**.

---

## Enhanced Logging and Security (Phase 1)

EchoNote implements enterprise-grade logging and user permission management for secure multi-user environments.

### Structured JSON Logging

**Production-Ready Logging System:**
- **JSON Structured Logs** - Machine-readable logs with `python-json-logger`
- **Log Rotation** - Automatic rotation at 10MB with 5 backup files
- **Multiple Log Streams** - Separate logs for app, errors, and security events
- **Audit Trail** - Comprehensive middleware for tracking all authenticated API requests

**Log Files** (`backend/logs/`):
- `app.log` - General application events (INFO level)
- `error.log` - Errors and exceptions (ERROR level)
- `security.log` - Authentication and authorization events
- Automatic rotation: `app.log.1`, `app.log.2`, etc.

**Security Audit Logging:**
Every authenticated API request is automatically logged with:
- User ID, username, email
- HTTP method, path, query parameters
- IP address, user agent
- Response status code and duration
- Sensitive data (passwords, tokens) automatically sanitized

**Example Log Entry:**
```json
{
  "timestamp": "2025-11-17T10:30:45.123Z",
  "level": "INFO",
  "event_type": "api_request",
  "user_id": 42,
  "username": "alice",
  "method": "POST",
  "path": "/api/transcribe",
  "status_code": 200,
  "duration_ms": 1234,
  "ip_address": "192.168.1.100"
}
```

### User Permissions and Quotas

**Role-Based Access Control (RBAC):**
- **User Role** - Standard users with daily AI action quotas
- **Admin Role** - Unlimited access, bypass all quota checks

**Daily AI Action Quotas:**
- Default quota: **100 AI actions per day** for standard users
- Automatic reset at midnight UTC via Celery Beat scheduler
- Actions tracked: transcriptions, AI summaries, AI actions
- Quota costs configurable per action type (e.g., transcription = 1, summary = 2)

**Quota Management:**
- Real-time quota checking before processing requests
- Automatic usage tracking and increment
- Detailed usage statistics API
- Admin users bypass all quota limits
- Premium users get higher quotas (configurable)

**API Quota Information:**
- `GET /api/auth/me` returns quota status:
  ```json
  {
    "id": 42,
    "username": "alice",
    "role": "user",
    "is_premium": false,
    "ai_action_quota_daily": 100,
    "ai_action_count_today": 23,
    "quota_reset_date": "2025-11-18"
  }
  ```

**Enforcement Decorators:**
```python
@require_quota(cost=1)  # Check quota before processing
@require_role("admin")  # Restrict to admin users only
@track_usage(action_type="transcription")  # Track usage
```

For detailed documentation on roles, quotas, and permissions, see **[ROLES_AND_QUOTAS.md](ROLES_AND_QUOTAS.md)**.

---

## AI Actions API (Phase 2)

EchoNote provides 18 AI-powered action endpoints to transform, analyze, and enhance your transcriptions. All endpoints enforce quota limits and track usage.

### Categories and Endpoints

**1. Analyze (1 endpoint, cost: 1 quota)**
- `POST /api/v1/actions/analyze` - Analyze transcription to extract summary, tasks, and next actions

**2. Create (4 endpoints, cost: 2 quota each)**
- `POST /api/v1/actions/create/linkedin-post` - Generate a LinkedIn post from transcription
- `POST /api/v1/actions/create/email-draft` - Generate an email draft from transcription
- `POST /api/v1/actions/create/blog-post` - Generate a blog post from transcription
- `POST /api/v1/actions/create/social-media-caption` - Generate social media captions

**3. Improve/Transform (7 endpoints, cost: 1 quota each)**
- `POST /api/v1/actions/improve/summarize` - Create a concise summary
- `POST /api/v1/actions/improve/summarize-bullets` - Create a bullet-point summary
- `POST /api/v1/actions/improve/rewrite-formal` - Rewrite in formal tone
- `POST /api/v1/actions/improve/rewrite-friendly` - Rewrite in friendly, casual tone
- `POST /api/v1/actions/improve/rewrite-simple` - Simplify for better accessibility
- `POST /api/v1/actions/improve/expand` - Expand with more detail and context
- `POST /api/v1/actions/improve/shorten` - Condense while preserving key points

**4. Translate (3 endpoints, cost: 1 quota each)**
- `POST /api/v1/actions/translate/to-english` - Translate to English
- `POST /api/v1/actions/translate/to-swedish` - Translate to Swedish
- `POST /api/v1/actions/translate/to-czech` - Translate to Czech

**5. Voice-Specific Utilities (3 endpoints, cost: 1 quota each)**
- `POST /api/v1/actions/voice/clean-filler-words` - Remove filler words (um, uh, like, etc.)
- `POST /api/v1/actions/voice/fix-grammar` - Correct grammatical errors
- `POST /api/v1/actions/voice/convert-spoken-to-written` - Convert spoken language to written prose

### Request/Response Format

**Request Body** (all endpoints):
```json
{
  "transcription_id": 123,
  "options": {
    "key": "value"
  }
}
```

**Response Format** (Phase 2 - work in progress):
```json
{
  "action_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "work_in_progress",
  "message": "endpoint analyze - work in progress to implement this functionality\n\nTranscription text: [full transcription text here]",
  "quota_remaining": 99,
  "quota_reset_date": "2025-11-19",
  "result": null,
  "error": null,
  "created_at": "2025-11-18T08:00:00",
  "completed_at": null
}
```

**Response includes:**
- `action_id`: Unique UUID for tracking this AI action
- `status`: Current status (work_in_progress, completed, failed)
- `message`: Status message including the transcription text for verification
- `quota_remaining`: How many actions the user has left today
- `quota_reset_date`: When quota resets (midnight UTC)
- `result`: AI-generated result (null in Phase 2)
- `error`: Error message if failed (null if successful)
- `created_at`: When action was initiated
- `completed_at`: When action completed (null if still processing)

### Usage Examples

**1. Analyze a transcription:**
```bash
TOKEN="your_jwt_token"
TRANSCRIPTION_ID=123

curl -X POST "http://localhost:8000/api/v1/actions/analyze" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"transcription_id\": $TRANSCRIPTION_ID, \"options\": {\"analysis_type\": \"summary\"}}" | python3 -m json.tool
```

**2. Create a LinkedIn post:**
```bash
curl -X POST "http://localhost:8000/api/v1/actions/create/linkedin-post" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"transcription_id\": $TRANSCRIPTION_ID, \"options\": {\"tone\": \"professional\", \"include_hashtags\": true}}" | python3 -m json.tool
```

**3. Summarize with bullet points:**
```bash
curl -X POST "http://localhost:8000/api/v1/actions/improve/summarize-bullets" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"transcription_id\": $TRANSCRIPTION_ID, \"options\": {\"max_bullets\": 5}}" | python3 -m json.tool
```

**4. Translate to Swedish:**
```bash
curl -X POST "http://localhost:8000/api/v1/actions/translate/to-swedish" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"transcription_id\": $TRANSCRIPTION_ID, \"options\": {}}" | python3 -m json.tool
```

**5. Clean filler words:**
```bash
curl -X POST "http://localhost:8000/api/v1/actions/voice/clean-filler-words" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"transcription_id\": $TRANSCRIPTION_ID, \"options\": {\"aggressiveness\": \"moderate\"}}" | python3 -m json.tool
```

### Quota Enforcement

All AI action endpoints:
- ✅ Check user quota before processing using `@require_quota(cost=N)` decorator
- ✅ Track usage automatically with `@track_usage(action_type="...")` decorator
- ✅ Return quota information in every response
- ✅ Admins bypass all quota checks
- ✅ Premium users can have higher quotas (configurable)

**Quota costs by category:**
- Analyze: 1 action
- Create (LinkedIn, email, blog, caption): 2 actions each
- Improve (summarize, rewrite, expand, shorten): 1 action each
- Translate: 1 action each
- Voice utilities: 1 action each

### Database Schema

**AI Actions Table** (`ai_actions`):
```sql
CREATE TABLE ai_actions (
    id INTEGER PRIMARY KEY,
    action_id VARCHAR(36) UNIQUE NOT NULL,  -- UUID v4
    user_id INTEGER NOT NULL,               -- Foreign key to users
    transcription_id INTEGER NOT NULL,      -- Foreign key to transcriptions
    action_type VARCHAR(100) NOT NULL,      -- e.g., 'analyze', 'create/linkedin-post'
    status VARCHAR(20) DEFAULT 'work_in_progress',
    request_params TEXT DEFAULT '{}',       -- JSON as TEXT
    result_data TEXT,                       -- JSON as TEXT (nullable)
    error_message VARCHAR(500),             -- Error details if failed
    quota_cost INTEGER DEFAULT 1,           -- How many actions this cost
    created_at DATETIME NOT NULL,
    completed_at DATETIME,                  -- When processing finished
    processing_duration_ms INTEGER,         -- Processing time in milliseconds

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (transcription_id) REFERENCES transcriptions(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_ai_actions_action_id ON ai_actions(action_id);
CREATE INDEX idx_ai_actions_user_id ON ai_actions(user_id);
CREATE INDEX idx_ai_actions_transcription_id ON ai_actions(transcription_id);
CREATE INDEX idx_ai_actions_action_type ON ai_actions(action_type);
CREATE INDEX idx_ai_actions_status ON ai_actions(status);
CREATE INDEX idx_ai_actions_created_at ON ai_actions(created_at);
```

**Migration:** Database migration `004_add_ai_actions.py` creates the `ai_actions` table with all indexes.

### Architecture

**Service Layer** (`backend/services/ai_action_service.py`):
- `create_action_record()` - Create AI action with UUID
- `get_user_actions()` - Paginated list with filters
- `get_action_by_id()` - Retrieve with ownership verification
- `verify_transcription_access()` - Check user owns transcription
- `get_action_statistics()` - Usage stats by type and time period

**Router** (`backend/routers/actions.py`):
- All 18 endpoints with standardized structure
- Quota enforcement via decorators
- Permission verification (user must own transcription)
- Standardized error handling
- Returns transcription text in response for verification

**Current Status (Phase 2):**
- ✅ Database schema implemented
- ✅ Service layer complete
- ✅ All 18 endpoints functional
- ✅ Quota enforcement active
- ✅ Permission checks working
- ✅ Returns dummy responses with transcription text
- ✅ Phase 3 supporting infrastructure complete

**Testing:**
```bash
# 1. Register and login
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"Test1234"}'

curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"Test1234"}'

# 2. Get your transcriptions
TOKEN="your_token_here"
curl -X GET "http://localhost:8000/api/transcriptions" \
  -H "Authorization: Bearer $TOKEN"

# 3. Test an AI action
TRANSCRIPTION_ID=1
curl -X POST "http://localhost:8000/api/v1/actions/analyze" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"transcription_id\": $TRANSCRIPTION_ID, \"options\": {}}"

# 4. Check your quota
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

For complete API testing documentation, see **[API_TEST_CURL.md](API_TEST_CURL.md)**.

---

## Admin & Monitoring (Phase 3)

Phase 3 provides comprehensive administrative and monitoring capabilities for managing users, tracking system health, and automating maintenance tasks.

### Admin Endpoints

All admin endpoints require admin role authentication (`role="admin"`).

**Base Path**: `/api/admin`

#### User Management

**List All Users**
```bash
GET /api/admin/users?skip=0&limit=20&role=user&search=john
```
- Pagination with skip/limit
- Filter by role (user, admin)
- Filter by premium status
- Search by username or email
- Returns user counts (transcriptions, AI actions)

**Get User Details**
```bash
GET /api/admin/users/{user_id}
```
- Complete user information
- Transcription statistics (total, this month)
- AI action statistics (total, this month, today, by type)

**Adjust User Quota**
```bash
PATCH /api/admin/users/{user_id}/quota
Content-Type: application/json

{
  "ai_action_quota_daily": 500
}
```

**Change User Role**
```bash
PATCH /api/admin/users/{user_id}/role
Content-Type: application/json

{
  "role": "admin"  # "user" or "admin"
}
```

**Toggle Premium Status**
```bash
PATCH /api/admin/users/{user_id}/premium
Content-Type: application/json

{
  "is_premium": true
}
```
- Automatically adjusts quota (1000 for premium, 100 for free)

**Activate/Deactivate User**
```bash
PATCH /api/admin/users/{user_id}/active
Content-Type: application/json

{
  "is_active": false
}
```

#### AI Actions Monitoring

**List All AI Actions**
```bash
GET /api/admin/actions?skip=0&limit=50&user_id=5&action_type=analyze&status=completed
```
- Filter by user, action type, status
- Filter by date range (date_from, date_to in ISO format)
- Ordered by creation date (newest first)

**System Statistics**
```bash
GET /api/admin/stats
```

Returns comprehensive system-wide statistics:
```json
{
  "users": {
    "total": 1000,
    "active": 950,
    "premium": 50,
    "admins": 2,
    "new_this_month": 100
  },
  "transcriptions": {
    "total": 50000,
    "this_month": 5000,
    "today": 200
  },
  "ai_actions": {
    "total": 250000,
    "this_month": 30000,
    "today": 1200,
    "by_type": {
      "analyze": 50000,
      "create/*": 40000,
      "improve/*": 100000,
      "translate/*": 40000,
      "voice/*": 20000
    },
    "by_status": {
      "completed": 240000,
      "failed": 5000,
      "work_in_progress": 5000
    }
  },
  "quotas": {
    "total_allocated": 100000,
    "used_today": 1200,
    "average_per_user": 12
  }
}
```

### User Usage Endpoints

Available to all authenticated users for tracking their own usage.

**Get Usage Statistics**
```bash
GET /api/auth/me/usage
Authorization: Bearer {token}
```

Returns:
```json
{
  "quota": {
    "daily_limit": 100,
    "used_today": 45,
    "remaining_today": 55,
    "reset_date": "2025-11-19",
    "is_premium": false
  },
  "usage_history": {
    "total_actions": 450,
    "this_month": 120,
    "this_week": 35,
    "today": 45
  },
  "breakdown_by_type": {
    "analyze": 10,
    "create/linkedin-post": 5,
    "improve/summarize": 20,
    "translate/to-english": 10
  }
}
```

**List My AI Actions**
```bash
GET /api/auth/me/actions?skip=0&limit=20&action_type=analyze&status=completed
Authorization: Bearer {token}
```
- Filter by action type, status
- Filter by date range (date_from, date_to in ISO format)
- Ordered by creation date (newest first)

**Get Specific Action Result**
```bash
GET /api/auth/me/actions/{action_id}
Authorization: Bearer {token}
```

Returns complete action details:
```json
{
  "action_id": "uuid-here",
  "action_type": "analyze",
  "status": "work_in_progress",
  "message": "endpoint analyze - work in progress...",
  "transcription_id": 123,
  "quota_cost": 1,
  "created_at": "2025-11-18T10:00:00Z",
  "completed_at": null,
  "result": null,
  "error": null
}
```

### Scheduled Maintenance Tasks

Celery Beat runs three automated maintenance tasks:

#### 1. Daily Quota Reset
**Task**: `reset_daily_quotas`
**Schedule**: Every day at 00:00 UTC
**Purpose**: Reset all users' `ai_action_count_today` to 0

```python
# Resets quota for all users
# Updates quota_reset_date
# Logs number of users reset
```

#### 2. Log Cleanup
**Task**: `cleanup_old_logs`
**Schedule**: Sunday at 02:00 UTC (weekly)
**Purpose**:
- Compress logs older than 90 days → `logs/archive/*.gz`
- Delete archived logs older than 180 days
- Saves disk space while maintaining audit trail

```bash
# Log directory structure
logs/
├── app.log
├── app.log.1, app.log.2, ...
├── security.log
├── security.log.1, security.log.2, ...
├── error.log
├── error.log.1, error.log.2, ...
└── archive/
    ├── app.log.1.gz
    └── security.log.1.gz
```

#### 3. AI Actions Cleanup
**Task**: `cleanup_old_ai_actions`
**Schedule**: Sunday at 03:00 UTC (weekly)
**Purpose**: Delete AI actions older than 30 days with status `completed` or `work_in_progress`

- Failed actions are kept for debugging
- Reduces database size
- Maintains recent history for analytics

### Default Admin User

On first startup, EchoNote automatically creates a default admin user:

```
Username: admin
Password: Admin1234
Email: admin@echonote.local
Role: admin
```

⚠️ **SECURITY WARNING**: Change this password immediately in production!

**Automatic Creation**:
- Created only if no admin users exist
- Runs during database initialization
- Logged to console on creation
- Has unlimited quota (999999 actions/day)

### Testing Admin Endpoints

**1. Login as Default Admin**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin1234"}' | python3 -m json.tool
```

**3. Test Admin Endpoints**
```bash
ADMIN_TOKEN="your_admin_token"

# List all users
curl -X GET "http://localhost:8000/api/admin/users" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | python3 -m json.tool

# Get system statistics
curl -X GET "http://localhost:8000/api/admin/stats" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | python3 -m json.tool

# View user details
curl -X GET "http://localhost:8000/api/admin/users/2" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | python3 -m json.tool

# Adjust user quota
curl -X PATCH "http://localhost:8000/api/admin/users/2/quota" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ai_action_quota_daily": 500}' | python3 -m json.tool

# Toggle premium status
curl -X PATCH "http://localhost:8000/api/admin/users/2/premium" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_premium": true}' | python3 -m json.tool

# List all AI actions
curl -X GET "http://localhost:8000/api/admin/actions?limit=10" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | python3 -m json.tool
```

**4. Test User Usage Endpoints**
```bash
USER_TOKEN="your_user_token"

# Get my usage statistics
curl -X GET "http://localhost:8000/api/auth/me/usage" \
  -H "Authorization: Bearer $USER_TOKEN" | python3 -m json.tool

# List my AI actions
curl -X GET "http://localhost:8000/api/auth/me/actions?limit=10" \
  -H "Authorization: Bearer $USER_TOKEN" | python3 -m json.tool

# Get specific action result
curl -X GET "http://localhost:8000/api/auth/me/actions/{action_id}" \
  -H "Authorization: Bearer $USER_TOKEN" | python3 -m json.tool
```

### Permission Model

**Role Hierarchy:**
- `admin`: Full access to all endpoints (bypasses quota checks)
- `user`: Standard user with quota limits

**Admin Capabilities:**
- View all users and their statistics
- Modify user quotas, roles, and status
- View all AI actions across all users
- Access system-wide statistics
- **Bypass** all quota checks
- All admin actions logged to security.log

**User Capabilities:**
- View own usage statistics
- View own AI actions
- Subject to daily quota limits
- Cannot access other users' data

### Architecture Notes

**Service Layer**:
- Admin operations logged to `security.log` with admin user context
- All admin actions include audit trail
- Permission checks at dependency level (`require_admin_role`)

**Database Queries**:
- Optimized joins for user/action listings
- Aggregation queries for statistics
- Proper indexing on user_id, action_type, created_at

**Scheduled Tasks**:
- Celery Beat schedule defined in `celery_app.py`
- Task names as strings (no imports needed for Beat)
- Workers import tasks at runtime
- Logging for all task executions

**Current Status (Phase 3):**
- ✅ Admin router with 9 endpoints
- ✅ User usage endpoints (3 endpoints)
- ✅ System statistics dashboard
- ✅ Celery scheduled tasks (3 tasks)
- ✅ Comprehensive audit logging
- ✅ Role-based access control
- ✅ Default admin user auto-creation
- ⏳ AI processing implementation (Phase 4)

**For complete Phase 3 testing instructions, see [PHASE3_TESTING.md](PHASE3_TESTING.md)**.

---

## Security Hardening (Phase 4)

Phase 4 implements comprehensive security hardening for production deployment, protecting against common attack vectors and enforcing security best practices.

### Security Features Implemented

**1. Configuration Validation** (`backend/main.py`)
- Startup validation prevents deployment with insecure settings
- **Blocks startup** if JWT_SECRET_KEY uses default values
- **Warns** about weak secrets, SQLite usage, CORS wildcards, DEBUG mode
- Tests file system permissions for logs/data directories
- Detailed error messages with actionable guidance

**2. Password Complexity** (`backend/models.py`)
Enhanced `UserCreate` with Pydantic validators:
- ✅ Minimum 8 characters
- ✅ Requires uppercase letter (A-Z)
- ✅ Requires lowercase letter (a-z)
- ✅ Requires digit (0-9)
- ✅ Email format validation (auto-converts to lowercase)
- ✅ Username format validation (alphanumeric + hyphens/underscores only)

**3. Rate Limiting** (`backend/middleware/rate_limiter.py`)
Redis-backed rate limiting to prevent abuse:
- **Login**: 5 attempts per 15 minutes per IP
- **Registration**: 3 attempts per hour per IP
- **Transcription**: 10 requests per minute per user
- **AI Actions**: 30 requests per minute per user
- Automatic retry-after headers in 429 responses
- Per-IP limiting for unauthenticated, per-user for authenticated

**4. Input Sanitization** (`backend/utils/sanitization.py`)
Comprehensive protection against injection attacks:
- `sanitize_text_input()` - XSS prevention with bleach
- `sanitize_filename()` - Path traversal prevention
- `sanitize_url()` - Dangerous protocol rejection (javascript:, data:)
- `sanitize_username()` & `sanitize_email()` - Format validation

**5. Failed Login Tracking** (`backend/services/auth_security_service.py`)
Account lockout to prevent brute force attacks:
- Tracks failed attempts per username (thread-safe, in-memory)
- **Locks account** after 5 failed attempts for 15 minutes
- Progressive warning messages ("4 attempts remaining...")
- Automatic unlock after timeout
- Clears attempts on successful login
- Detailed security logging

### Security Best Practices Enforced

**Environment Security**:
```bash
# .env.example template with security documentation
- JWT_SECRET_KEY must be changed (errors if default)
- PostgreSQL recommended over SQLite (warns if SQLite)
- CORS wildcard detection (warns if "*")
- DEBUG mode detection (warns if enabled)
```

**Authentication Security**:
```python
# Strong password requirements
Password: "Test123"     # ✅ Valid (uppercase, lowercase, digit)
Password: "password"    # ❌ Rejected (no uppercase or digit)
Password: "PASSWORD1"   # ❌ Rejected (no lowercase)
Password: "Test"        # ❌ Rejected (too short)

# Account lockout after failed attempts
Attempt 1-4: "Incorrect password. X attempts remaining..."
Attempt 5:   "Account locked for 15 minutes"
Locked:      "Account temporarily locked. Try again in X minutes."
```

**Rate Limiting**:
```bash
# Login brute force protection
POST /api/auth/login (6th attempt in 15min)
→ 429 Too Many Requests
→ { "detail": "Rate limit exceeded", "retry_after": 900 }

# Registration spam prevention
POST /api/auth/register (4th attempt in 1 hour)
→ 429 Too Many Requests
```

**Input Sanitization**:
```python
# XSS attack prevention
Input:  "<script>alert('XSS')</script>Hello"
Output: "Hello"  # Script tag removed

# Path traversal prevention
Input:  "../../../etc/passwd"
Output: "etcpasswd"  # Path separators removed

# URL protocol validation
Input:  "javascript:alert('XSS')"
Output: None  # Rejected (dangerous protocol)
```

### Security Logging

All security events are logged to `backend/logs/security.log`:

```json
{
  "timestamp": "2025-11-18T10:30:00.123Z",
  "level": "WARNING",
  "message": "Failed login attempt for 'testuser' (3/5)",
  "event_type": "failed_login",
  "username": "testuser",
  "attempts": 3,
  "attempts_remaining": 2
}
```

**Events Logged**:
- User registration
- Login success/failure
- Failed login attempts with counter
- Account lockouts and unlocks
- Configuration validation warnings/errors
- Rate limit violations

### Production Deployment Checklist

Before deploying to production:

- [ ] Generate secure JWT secret: `python3 -c "import secrets; print(secrets.token_urlsafe(64))"`
- [ ] Set `JWT_SECRET_KEY` in `.env` (minimum 64 characters)
- [ ] Configure PostgreSQL (not SQLite): `DATABASE_URL=postgresql://...`
- [ ] Set CORS to production domains only: `CORS_ORIGINS=https://yourdomain.com`
- [ ] Set `LOG_LEVEL=INFO` or `WARNING` (not DEBUG)
- [ ] Ensure Redis is running for rate limiting
- [ ] Set `DB_ECHO=false` (disable SQL query logging)
- [ ] Remove `DEBUG=true` from environment
- [ ] Test failed login lockout behavior
- [ ] Verify password complexity requirements
- [ ] Review and test rate limits for your use case
- [ ] Set up HTTPS/TLS at reverse proxy level

### Testing Security Features

**Quick Security Test**:
```bash
# Test password complexity
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@test.com","password":"weak"}'
# Expected: Error "Password must be at least 8 characters long"

# Test rate limiting (run 6 times rapidly)
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"wrong"}' \
    -w "\nHTTP: %{http_code}\n"
done
# Expected: Attempts 1-5 return 401, attempt 6 returns 429

# Test account lockout (5 failed attempts)
# After 5 failures, even correct password returns 403 for 15 minutes
```

### Dependencies Added

```python
# backend/requirements.txt
slowapi==0.1.9   # Rate limiting for FastAPI
bleach==6.0.0    # HTML sanitization to prevent XSS attacks
```

### Documentation

- **[PHASE4_SECURITY_TESTING.md](PHASE4_SECURITY_TESTING.md)** - Comprehensive testing guide with 20+ test scenarios
- **[PHASE4_IMPLEMENTATION_SUMMARY.md](PHASE4_IMPLEMENTATION_SUMMARY.md)** - Complete implementation documentation
- **[backend/.env.example](backend/.env.example)** - Environment template with security documentation

### Security Improvements Summary

| Security Risk | Before Phase 4 | After Phase 4 |
|---------------|----------------|---------------|
| Brute Force Attacks | ⚠️ No protection | ✅ Rate limiting + account lockout |
| XSS Attacks | ⚠️ No sanitization | ✅ Bleach HTML sanitization |
| Path Traversal | ⚠️ No validation | ✅ Filename sanitization |
| Weak Passwords | ⚠️ No requirements | ✅ Complexity validation |
| Insecure Deployment | ⚠️ No validation | ✅ Startup configuration checks |
| API Abuse | ⚠️ No rate limits | ✅ Comprehensive rate limiting |

**Current Status (Phase 4):**
- ✅ Configuration validation with startup checks
- ✅ Password complexity enforcement
- ✅ Rate limiting (login, registration, API endpoints)
- ✅ Input sanitization (XSS, path traversal, URL validation)
- ✅ Failed login tracking with account lockout
- ✅ Comprehensive security logging
- ✅ Production-ready security posture

---

## Tech Stack

### Backend
- **FastAPI** - Modern, fast web framework for building APIs
- **SQLModel** - SQL databases using Python type hints
- **SQLite** - Development database (auto-created)
- **PostgreSQL** - Production database support
- **Celery 5.5.3** - Distributed task queue for async transcription processing
- **Redis 7** - Message broker and result backend for Celery
- **PyJWT** - JWT token generation and validation
- **Passlib** - Password hashing with bcrypt
- **slowapi** - Rate limiting for FastAPI (Phase 4: Security)
- **bleach** - HTML sanitization to prevent XSS attacks (Phase 4: Security)
- **OpenAI SDK** - For Whisper API calls to vLLM server
- **pyannote.audio** - Speaker diarization (CPU-only PyTorch)
- **pydub** - Audio chunking for long recordings (60s+ segments)

### Frontend
- **Vite** - Next generation frontend tooling
- **React 18** - UI library with hooks
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **MediaRecorder API** - Browser-native audio recording
- **Service Worker** - PWA offline functionality and caching
- **IndexedDB** - Client-side storage for offline recordings
- **Background Sync** - Automatic upload retry when online

## Project Structure

```
echonote/
├── backend/
│   ├── Containerfile         # Backend container build (UBI 10 Python)
│   ├── Containerfile.celery  # Celery worker container build
│   ├── Containerfile.celery-beat  # Celery Beat scheduler container build
│   ├── .containerignore      # Backend build exclusions
│   ├── .env.example          # Environment template with security docs - Phase 4
│   ├── requirements.txt      # Python dependencies (full, includes slowapi + bleach)
│   ├── requirements-beat.txt # Minimal dependencies for Beat scheduler
│   ├── __init__.py
│   ├── main.py               # FastAPI app (lifespan, routers, config validation - Phase 4)
│   ├── routers/              # API endpoint routers (modular)
│   │   ├── __init__.py
│   │   ├── health.py         # Health check endpoints
│   │   ├── transcriptions.py # Transcription endpoints (rate limited - Phase 4)
│   │   ├── actions.py        # AI Actions endpoints (18 endpoints, rate limited - Phase 4)
│   │   └── admin.py          # Admin endpoints (9 endpoints) - Phase 3
│   ├── services/             # Business logic layer
│   │   ├── __init__.py
│   │   ├── transcription_service.py     # Transcription business logic
│   │   ├── permission_service.py        # Quota management & role checking
│   │   ├── ai_action_service.py         # AI Actions business logic
│   │   └── auth_security_service.py     # Failed login tracking - Phase 4
│   ├── middleware/           # Request/response middleware
│   │   ├── __init__.py
│   │   ├── audit_logger.py   # Security audit logging middleware
│   │   ├── quota_checker.py  # Quota enforcement decorators
│   │   └── rate_limiter.py   # Rate limiting middleware - Phase 4
│   ├── utils/                # Utility functions
│   │   └── sanitization.py   # Input sanitization (XSS, path traversal) - Phase 4
│   ├── models.py             # SQLModel models & schemas (password validators - Phase 4)
│   ├── database.py           # Database config, session mgmt & default admin creation
│   ├── config.py             # Application settings
│   ├── auth.py               # Authentication utilities (JWT, password hashing)
│   ├── auth_routes.py        # Auth endpoints (register, login, usage, rate limited - Phase 4)
│   ├── logging_config.py     # Structured JSON logging configuration
│   ├── celery_app.py         # Celery app config & Beat schedule - Phase 3
│   ├── tasks.py              # Celery tasks (transcription, quota, cleanup) - Phase 3
│   ├── audio_chunker.py      # Audio chunking for long recordings
│   ├── transcription_merger.py  # Merge chunked transcription results
│   ├── diarization.py        # Speaker diarization service
│   ├── alembic/              # Database migrations
│   │   ├── versions/
│   │   │   ├── 001_initial_schema.py
│   │   │   ├── 002_add_authentication.py
│   │   │   ├── 003_add_user_quotas_and_permissions.py
│   │   │   └── 004_add_ai_actions.py
│   │   └── env.py
│   └── logs/                 # Application logs (auto-created, gitignored)
│       ├── app.log           # General application logs
│       ├── error.log         # Error logs
│       └── security.log      # Security audit logs (login attempts, lockouts - Phase 4)
├── frontend/
│   ├── Containerfile       # Frontend container build (UBI 10 Node.js)
│   ├── .containerignore    # Frontend build exclusions
│   ├── .gitignore          # Frontend git ignores
│   ├── package.json
│   ├── src/
│   │   ├── components/
│   │   │   ├── AudioRecorder.tsx
│   │   │   ├── TranscriptionList.tsx
│   │   │   └── Login.tsx           # Login/register page
│   │   ├── contexts/
│   │   │   └── AuthContext.tsx     # Authentication context
│   │   ├── hooks/
│   │   │   └── useTranscriptionPolling.ts  # Real-time status polling hook
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── api.ts          # API client with JWT token support
│   │   ├── types.ts        # TypeScript types
│   │   └── index.css
│   ├── index.html
│   ├── vite.config.ts
│   └── tailwind.config.js
├── redis/
│   ├── Containerfile       # Redis container build
│   └── redis.conf          # Redis configuration (no RDB persistence)
├── echonote-kube.yaml      # Legacy deployment (2 containers - NOT FUNCTIONAL)
├── echonote-kube-priv.yaml # Production deployment (4 containers - REQUIRED)
├── .gitignore              # Project-level git ignores
├── CONTAINER.md            # Container deployment guide
├── AI_PLAN.md              # AI Actions implementation plan (Phases 1-4)
├── ROLES_AND_QUOTAS.md     # User roles and quota system documentation
├── API_TEST_CURL.md        # API testing examples with curl
├── PHASE3_TESTING.md       # Complete Phase 3 testing guide
├── PHASE4_SECURITY_TESTING.md        # Phase 4 security testing guide - NEW
├── PHASE4_IMPLEMENTATION_SUMMARY.md  # Phase 4 implementation docs - NEW
├── .env.example
└── README.md
```

## Architecture Overview

EchoNote follows modern **layered architecture** and **2025 FastAPI best practices** with clear separation of concerns:

### Backend Architecture Layers

**1. API Layer** (`backend/routers/`)
- Thin controllers that handle HTTP requests/responses
- Route registration and validation
- Delegates business logic to service layer
- **Routers**: `health`, `transcriptions`, `actions` (18 endpoints), `admin` (9 endpoints)

**2. Service Layer** (`backend/services/`)
- Contains all business logic
- Reusable, testable functions
- Independent of HTTP/API concerns
- **Services**: `TranscriptionService`, `PermissionService`, `AIActionService`

**3. Data Layer** (`backend/models.py`, `backend/database.py`)
- SQLModel database models
- API schemas (Create, Read, Update)
- Database session management
- **Auto-initialization**: Default admin user creation on first startup

**4. Authentication & Authorization** (`backend/auth.py`, `backend/auth_routes.py`)
- JWT token generation/validation
- Password hashing with bcrypt
- Dependency injection for protected endpoints
- **Role-based access control**: admin vs user permissions
- **User usage endpoints**: Self-service quota monitoring (Phase 3)

### Key Design Patterns

✅ **Lifespan Context Manager** - Modern startup/shutdown event handling
✅ **Dependency Injection** - FastAPI dependencies for auth, database sessions
✅ **Service Layer Pattern** - Business logic separated from API endpoints
✅ **Repository Pattern** - Database operations centralized
✅ **Schema Separation** - Different models for Create/Read/Update operations

## Background Processing Architecture

EchoNote uses a distributed task queue architecture for async transcription processing, providing a responsive user experience with real-time status updates.

### System Components

**5-Container Architecture:**
1. **Frontend** (`echonote-frontend`) - React/Vite SPA
2. **Backend** (`echonote-backend`) - FastAPI REST API (modular routers + service layer)
3. **Redis** (`echonote-redis`) - Message broker (db 0) & result backend (db 1)
4. **Celery Worker** (`echonote-celery-worker`) - Background task processor for transcriptions
5. **Celery Beat** (`echonote-celery-beat`) - Scheduler for periodic maintenance tasks (Phase 3)

**Celery Beat Scheduler (Phase 3):**
- Lightweight scheduler container with minimal dependencies (~400MB vs worker's ~2GB)
- Sends scheduled tasks to Redis queue at specified times
- **Scheduled Tasks**:
  - Daily quota reset (00:00 UTC) - Resets all users' daily quotas
  - Log cleanup (Sunday 02:00 UTC) - Archives old logs, deletes ancient archives
  - AI actions cleanup (Sunday 03:00 UTC) - Removes old completed actions
- Does not execute tasks - only schedules them
- Proper separation following official Celery best practices
- See [CELERY_ARCHITECTURE.md](CELERY_ARCHITECTURE.md) for detailed architecture documentation

### How It Works

**1. User Records Audio**
- Frontend captures audio using MediaRecorder API
- WebM audio is sent to backend `/api/transcribe` endpoint

**2. Backend Creates Task** (`backend/routers/transcriptions.py` → `backend/services/transcription_service.py`)
```python
POST /api/transcribe
├─ Router validates request (transcriptions.py)
├─ Service processes audio (transcription_service.py)
│   ├─ Validate file type and size
│   ├─ Convert WebM to WAV if needed
│   ├─ Extract duration
│   └─ Save to database with status="pending"
├─ Service dispatches Celery task
├─ Router returns transcription with status
└─ User sees instant feedback (no waiting for transcription)
```

**3. Celery Worker Processes** (`backend/tasks.py`)
```python
transcribe_audio_task(transcription_id, model, enable_diarization, ...)
├─ Load audio from database
├─ Check duration: if > 60s, chunk into 60s segments
├─ For each chunk:
│   ├─ Update progress: 10%, 30%, 50%, etc.
│   ├─ Call Whisper API via vLLM
│   └─ Save partial results
├─ Merge all chunks
├─ Update database: status="completed", text=final_transcription
└─ Worker reports completion
```

**4. Frontend Polls for Updates** (`frontend/src/hooks/useTranscriptionPolling.ts`)
```typescript
useTranscriptionPolling(pendingIds, enabled, onComplete, onStatusUpdate)
├─ Every 2 seconds: GET /api/transcriptions/status/bulk?ids=1,2,3
├─ Receive: [{ id: 1, status: "processing", progress: 45 }, ...]
├─ Merge status updates into React state
├─ UI automatically shows progress bars
└─ When completed: fetch full transcription with text
```

**5. UI Auto-Updates**
- Progress bar shows real-time completion percentage
- Status changes: pending → processing → completed
- Text appears automatically when done (no refresh needed!)

### Key Features

**Audio Chunking:**
- Recordings > 60 seconds are split into chunks
- Each chunk transcribed separately
- Results merged intelligently with timestamps
- Prevents API timeouts and memory issues

**Speaker Diarization:**
- Optional pyannote.audio integration
- Chunks aligned with speaker boundaries
- Output shows speaker timeline: "Speaker 1 (0:00-0:15): Hello..."

**Error Handling:**
- Failed chunks don't crash entire transcription
- Partial results saved
- Detailed error messages in UI
- Audio always preserved even if transcription fails

**Real-time Status:**
- Polling hook updates every 2s
- Only polls pending/processing transcriptions
- Automatic cleanup when all complete
- Minimal network overhead

### Configuration

**Redis Settings** (`.env`):
```bash
REDIS_URL=redis://localhost:6379/0           # Celery broker
CELERY_BROKER_URL=redis://localhost:6379/0   # Message queue
CELERY_RESULT_BACKEND=redis://localhost:6379/1  # Task results
```

**Chunking Settings** (`.env`):
```bash
CHUNK_DURATION_SECONDS=60        # Split audio into 60s chunks
MAX_AUDIO_DURATION_SECONDS=3600  # Max 1 hour recordings
```

**Celery Worker Settings** (`backend/celery_app.py`):
```python
celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,        # 1 hour hard limit per task
    task_soft_time_limit=3300,   # 55 min soft limit
)
```

### API Endpoints

**Start Transcription:**
```bash
POST /api/transcribe
Body: multipart/form-data (file, model, enable_diarization, num_speakers)
Response: { id: 123, status: "pending", progress: 0, task_id: "abc-123", ... }
```

**Check Status (Single):**
```bash
GET /api/transcriptions/123/status
Response: { id: 123, status: "processing", progress: 45, error_message: null }
```

**Check Status (Bulk):**
```bash
GET /api/transcriptions/status/bulk?ids=1,2,3
Response: { statuses: [{ id: 1, status: "completed", progress: 100 }, ...] }
```

**Get Completed Transcription:**
```bash
GET /api/transcriptions/123
Response: { id: 123, text: "Full transcription...", status: "completed", ... }
```

### Monitoring & Debugging

**Check Celery Worker:**
```bash
podman logs echonote-celery-worker
# Should see: "celery@echonote ready"
```

**Check Redis:**
```bash
podman exec echonote-redis redis-cli ping
# Should return: PONG
```

**Monitor Tasks:**
```bash
# Check queued tasks
podman exec echonote-redis redis-cli -n 0 keys "celery*"

# Check task results
podman exec echonote-redis redis-cli -n 1 keys "*"
```

**Frontend Console (Browser DevTools):**
```javascript
// Enable debug logging in browser console
// You'll see detailed polling and state update logs
[App] Pending IDs for polling: [123, 124]
[useTranscriptionPolling] Starting poll for IDs: [123, 124]
[useTranscriptionPolling] Poll response: { statuses: [...] }
[App] handleStatusUpdate called with statuses: [...]
[App] Updating transcription 123: { oldStatus: "pending", newStatus: "processing", oldProgress: 0, newProgress: 25 }
```

### Troubleshooting

**Problem: UI not updating, transcriptions stuck in "pending"**
- Check if Celery worker is running: `podman ps | grep celery`
- Check Celery logs: `podman logs echonote-celery-worker`
- Verify Redis connection: `podman exec echonote-redis redis-cli ping`

**Problem: Transcription completes but UI doesn't show text**
- Check browser console for polling logs
- Verify `/api/transcriptions/{id}` returns status fields
- Ensure frontend is polling: watch for "Starting poll for IDs" in console

**Problem: Long recordings fail or timeout**
- Check `CHUNK_DURATION_SECONDS` is set (default: 60)
- Verify audio chunking is working in Celery logs
- Increase `task_time_limit` if needed (default: 3600s)

**Problem: Redis connection errors**
- Ensure Redis container is running
- Check Redis configuration in `redis/redis.conf`
- Verify `REDIS_URL` and `CELERY_BROKER_URL` match Redis hostname

## Quick Start

### Prerequisites

- Python 3.10 or higher
- Node.js 20 or higher
- Access to a vLLM server running Whisper (or use the default endpoint)

**Note:** Audio is recorded in WebM format in the browser and sent directly to the backend. The server handles WebM to WAV conversion using FFmpeg in an isolated subprocess to ensure compatibility with the Whisper API and PyTorch/pyannote diarization pipeline.

### 1. Clone and Setup

```bash
git clone <repository-url>
cd echonote
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Create environment file
cp .env.example .env
# Edit .env to configure your settings

# Run backend (from project root)
python -m backend.main
```

The backend will start at `http://localhost:8000`

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend will start at `http://localhost:5173`

### 4. Access the Application

Open your browser and navigate to `http://localhost:5173`

### 5. First-time Setup

When you first access the application, you'll need to create an account:
1. Click "Sign up" on the login page
2. Enter a username, email, and password
3. Click "Create Account"
4. You'll be automatically logged in and redirected to the main application

## Configuration

### Environment Variables

Create a `.env` file in the project root (copy from `.env.example`):

```bash
# Whisper/vLLM Configuration
MODEL_URL=https://your-vllm-server.com/v1
MODEL_NAME=whisper-large-v3-turbo-quantizedw4a16
API_KEY=EMPTY

# Database Configuration
# Development (SQLite - default)
SQLITE_DB=echonote.db

# Production (PostgreSQL)
# DATABASE_URL=postgresql://user:password@localhost:5432/echonote

# Server Configuration
BACKEND_PORT=8000
BACKEND_HOST=0.0.0.0

# CORS Configuration
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Speaker Diarization (Optional)
# Get your token at: https://huggingface.co/settings/tokens
# Accept license at: https://huggingface.co/pyannote/speaker-diarization-3.1
# See SPEAKER_DIARIZATION.md for setup guide and troubleshooting
HF_TOKEN=your_huggingface_token_here
DIARIZATION_MODEL=pyannote/speaker-diarization-3.1

# Pagination Configuration
# Number of transcriptions to show per page (default: 10)
DEFAULT_PAGE_SIZE=10
# Maximum allowed page size (default: 100)
MAX_PAGE_SIZE=100

# JWT Authentication Configuration
# IMPORTANT: Change JWT_SECRET_KEY in production! Generate with: openssl rand -hex 32
JWT_SECRET_KEY=your-secret-key-change-this-in-production-use-openssl-rand-hex-32
JWT_ALGORITHM=HS256
# Token expiration in days (default: 30)
ACCESS_TOKEN_EXPIRE_DAYS=30
```

### Database Configuration

**Development (SQLite)**:
- No additional setup required
- Database file is auto-created as `echonote.db`

**Production (PostgreSQL)**:
1. Create a PostgreSQL database
2. Set `DATABASE_URL` environment variable:
   ```bash
   DATABASE_URL=postgresql://user:password@localhost:5432/echonote
   ```

## API Documentation

Once the backend is running, visit:
- Interactive API docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

### Main Endpoints

#### Authentication
- `POST /api/auth/register` - Register a new user account
  - **Body** (JSON):
    - `username`: Username (3-50 characters, unique)
    - `email`: Email address (unique)
    - `password`: Password (minimum 6 characters)
  - **Returns**: User object (without password)
  - **Status codes**: 201 Created, 400 Bad Request (if username/email exists)

- `POST /api/auth/login` - Login with username and password
  - **Body** (JSON):
    - `username`: Username
    - `password`: Password
  - **Returns**: JWT access token
  - **Status codes**: 200 OK, 401 Unauthorized

- `GET /api/auth/me` - Get current authenticated user information
  - **Headers**: `Authorization: Bearer <token>`
  - **Returns**: User object
  - **Status codes**: 200 OK, 401 Unauthorized

#### Health & Configuration
- `GET /` - Health check endpoint
  - Returns app status and version info
- `GET /api/models` - Get available transcription models
  - **Headers**: `Authorization: Bearer <token>`
  - Returns list of available models and default model

#### Transcription
- `POST /api/transcribe` - Upload and transcribe audio file (requires authentication)
  - **Headers**: `Authorization: Bearer <token>`
  - **Body** (multipart/form-data):
    - `file`: Audio file (required)
    - `url`: Optional URL associated with the voice note
    - `model`: Model to use for transcription (defaults to DEFAULT_MODEL)
    - `enable_diarization`: Enable speaker diarization (default: false)
    - `num_speakers`: Number of speakers (optional, auto-detect if not specified)
  - **Returns**: Transcription object with ID, text, metadata (includes speaker timeline if diarization enabled)
  - **Supported audio types**: audio/wav, audio/webm, audio/mp3, audio/mpeg
  - **Note**: Transcription is automatically associated with the authenticated user

#### Listing & Retrieval
- `GET /api/transcriptions` - List user's transcriptions (paginated, requires authentication)
  - **Headers**: `Authorization: Bearer <token>`
  - **Query params**:
    - `skip`: Number of records to skip (default: 0)
    - `limit`: Maximum records to return (defaults to DEFAULT_PAGE_SIZE, max: MAX_PAGE_SIZE)
    - `priority`: Filter by priority (low, medium, high)
  - **Returns**: List of user's transcriptions with total count
  - **Note**: Only returns transcriptions owned by the authenticated user

- `GET /api/transcriptions/{id}` - Get specific transcription (requires authentication)
  - **Headers**: `Authorization: Bearer <token>`
  - **Returns**: Transcription details without audio data
  - **Authorization**: User must own the transcription (403 Forbidden otherwise)

- `GET /api/transcriptions/{id}/audio` - Download audio file (requires authentication)
  - **Headers**: `Authorization: Bearer <token>`
  - **Returns**: Binary audio file
  - **Authorization**: User must own the transcription (403 Forbidden otherwise)
  - **Note**: For HTML `<audio>` elements, append token as query parameter: `/audio?token=<jwt_token>`

- `GET /api/transcriptions/{id}/download` - Download transcription package (requires authentication)
  - **Headers**: `Authorization: Bearer <token>`
  - **Returns**: ZIP file containing:
    - `{username}.wav`: Audio file in WAV format
    - `config.json`: Configuration file with transcript and audio filename
  - **Authorization**: User must own the transcription (403 Forbidden otherwise)
  - **ZIP filename**: `transcription_{id}_{username}.zip`
  - **config.json format**:
    ```json
    {
      "username": {
        "transcript": "Full transcription text here",
        "audio_file": "username.wav"
      }
    }
    ```
  - **Note**: Audio is automatically converted to WAV format if stored in another format

#### Updates & Deletion
- `PATCH /api/transcriptions/{id}` - Update transcription priority (requires authentication)
  - **Headers**: `Authorization: Bearer <token>`
  - **Query params**:
    - `priority`: New priority value (low, medium, high)
  - **Returns**: Updated transcription object
  - **Authorization**: User must own the transcription (403 Forbidden otherwise)

- `DELETE /api/transcriptions/{id}` - Delete transcription (requires authentication)
  - **Headers**: `Authorization: Bearer <token>`
  - **Returns**: Success message
  - **Authorization**: User must own the transcription (403 Forbidden otherwise)

## Error Handling & Debugging

### Transcription Failure Handling

EchoNote is designed to preserve your audio recordings even when transcription fails. This ensures you never lose your voice notes due to temporary issues.

**Behavior:**
- ✅ **Audio is always saved** - Even if transcription fails, the audio recording is stored in the database
- 📝 **Error message in transcript** - Failed transcriptions show a detailed error message instead of text
- 📊 **Detailed logging** - All errors are logged with full context for debugging

**Common transcription failures:**
1. **File size/duration limits** - Recording exceeds model's maximum input size
2. **Unsupported format** - Audio format not supported by transcription service
3. **Service unavailable** - vLLM server is down or unreachable
4. **Model context exceeded** - Recording too long for model's context window

**What gets logged:**

```
INFO: Processing audio file: recording.webm
INFO: Original file size: 15728640 bytes (15.00 MB)
INFO: Content type: audio/webm
INFO: Audio duration: 540.25 seconds (9.00 minutes)
INFO: WebM converted to WAV: 17280000 bytes (16.48 MB)
ERROR: Transcription API call failed: Error code: 400 - Maximum file size exceeded
WARNING: Saving recording without transcription due to error: Maximum file size exceeded
WARNING: Recording saved with ID: 123 (transcription failed: Maximum file size exceeded)
```

**User experience:**
- Recording appears in transcription list immediately
- Text shows `[TRANSCRIPTION FAILED]` with error details and helpful suggestions
- Audio file is fully playable and downloadable
- User can retry by re-recording with shorter duration

**For developers:**
- Check backend logs for detailed file size, duration, and error information
- Monitor for patterns (e.g., all 9+ minute recordings failing)
- Adjust vLLM configuration or implement chunking for long recordings

## Development

### Running Backend in Development

```bash
# From project root
python -m backend.main

# With auto-reload
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Frontend in Development

```bash
cd frontend
npm run dev
```

### Building for Production

**Backend**:
```bash
# No build step required for Python
# Just ensure all dependencies are installed
pip install -r requirements.txt
```

**Frontend**:
```bash
cd frontend
npm run build
# Build output will be in frontend/dist/
```

## Deployment

### Backend Deployment

1. **Set up PostgreSQL database**
2. **Configure environment variables**
3. **Run with a production server**:

```bash
pip install gunicorn
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Frontend Deployment

1. **Build the frontend**:
   ```bash
   cd frontend
   npm run build
   ```

2. **Serve the `dist` folder** with any static file server:
   - Nginx
   - Caddy
   - Vercel
   - Netlify
   - Cloudflare Pages

### Environment-Specific Configuration

**Railway/Render/Heroku**:
- Set `DATABASE_URL` to your PostgreSQL connection string
- These platforms usually auto-detect and convert `postgres://` to `postgresql://`

## PWA Installation

### Install as App

**Mobile (Android)**:
1. Open EchoNote in Chrome/Edge
2. Tap menu (⋮) → "Install app" or "Add to Home screen"
3. App appears on home screen with custom icon

**Mobile (iOS)**:
1. Open EchoNote in Safari
2. Tap Share (⬆) → "Add to Home Screen"
3. Tap "Add"

**Desktop**:
1. Look for install icon (⊕) in browser address bar
2. Click "Install"
3. App opens in standalone window

### Offline Mode

**Recording Offline**:
1. Record voice messages even without internet
2. Recordings are saved to local IndexedDB
3. Sync indicator shows "X pending"

**Automatic Sync**:
- When online, recordings automatically sync
- Manual sync: Click "Sync now" on sync indicator
- Failed recordings are skipped, not blocking queue

**Sync Status**:
- **Green checkmark**: All synced
- **Yellow syncing**: Upload in progress
- **Red offline**: Device is offline
- **Number badge**: Pending recordings count

---

## Usage

1. **First-time setup**:
   - Visit the application at `http://localhost:5173`
   - Click "Don't have an account? Sign up"
   - Enter your username, email, and password
   - Click "Create Account" to register and automatically log in

2. **Login**:
   - Enter your username and password
   - Click "Sign In"
   - Your JWT token is stored securely in browser localStorage

3. **Record a voice message**:
   - Adjust recording options (model, diarization) if desired
   - Click the large microphone button to start recording
   - Speak your message
   - Click the microphone button again to stop and transcribe

4. **Enable speaker diarization** (optional):
   - Check the "Enable speaker diarization" checkbox before recording
   - Optionally specify the number of speakers (leave empty for auto-detection)
   - The transcription will include a speaker timeline showing who spoke when

5. **Search and filter transcriptions**:
   - **Search**: Type keywords in the search box to find specific content in your transcriptions
   - Search is case-insensitive and searches the full text
   - **Filter**: Use priority buttons (All, High, Medium, Low) to filter by priority level
   - Search and filters work together - you can search within a specific priority
   - Clear search by clicking the X button or clearing the text

6. **View transcriptions**:
   - All your transcriptions appear in the list below
   - Click on any transcription to expand it
   - View full text and play audio
   - If diarization was enabled, see the speaker timeline
   - Delete unwanted transcriptions
   - **Note**: You can only see and manage your own transcriptions

7. **Play audio**:
   - Expand a transcription
   - Click the play button or use the audio controls

8. **Download transcriptions**:
   - Expand any transcription
   - Click the blue "Download" button
   - A ZIP file will be downloaded containing:
     - `{username}.wav`: Your audio recording in WAV format
     - `config.json`: Transcript text and metadata
   - The download includes your complete transcription and high-quality audio
   - Works from both the web UI and the API
   - **Use case**: Archive recordings, share with others, or integrate with other tools

9. **Logout**:
   - Click the "Logout" button in the header (desktop)
   - On mobile, scroll to show the footer and tap "Logout"
   - Your token will be cleared and you'll return to the login page

## Troubleshooting

### Audio Format Conversion
Audio is recorded in WebM format in the browser and sent directly to the backend. The server converts WebM to WAV using FFmpeg/pydub in an isolated subprocess.

If you see conversion errors:
- Ensure the recording completed successfully (check browser console for errors)
- Verify FFmpeg is installed on the server (required for conversion)
- Check server logs for conversion errors
- Try recording a shorter clip to test

### Microphone Access
- Ensure you've granted microphone permissions in your browser
- HTTPS is required for microphone access (except localhost)

### Backend Connection Issues
```bash
# Check if backend is running
curl http://localhost:8000

# Check CORS configuration in .env
CORS_ORIGINS=http://localhost:5173
```

### Authentication Issues
```bash
# 401 Unauthorized errors
# - Ensure you're logged in
# - Check if token is present in browser localStorage (key: echonote_token)
# - Try logging out and logging in again

# 403 Forbidden errors
# - You're trying to access another user's transcription
# - Ensure you're accessing your own transcriptions

# Token expiration
# - Default token lifetime is 30 days (configurable via ACCESS_TOKEN_EXPIRE_DAYS)
# - Expired tokens require re-login

# JWT Secret Key in Production
# - MUST change JWT_SECRET_KEY in production!
# - Generate a secure key: openssl rand -hex 32
# - Set in .env file before deployment
```

### Database Issues
```bash
# SQLite permissions
chmod 644 echonote.db

# PostgreSQL connection
# Verify DATABASE_URL format: postgresql://user:pass@host:port/db
```

### vLLM/Whisper Connection
```bash
# Test the Whisper endpoint
curl -X POST "https://your-vllm-server.com/v1/audio/transcriptions" \
  -H "Authorization: Bearer EMPTY" \
  -F "file=@test.wav" \
  -F "model=whisper-large-v3-turbo-quantizedw4a16"
```

### Speaker Diarization Issues

For detailed speaker diarization setup, troubleshooting, and version compatibility information, see **[SPEAKER_DIARIZATION.md](SPEAKER_DIARIZATION.md)**.

**Common issues:**

```bash
# Missing Hugging Face token
# Error: "pyannote models require a Hugging Face token"
# Solution: Set HF_TOKEN in your .env file

# License not accepted
# Error: "Cannot access gated model"
# Solution: Visit https://huggingface.co/pyannote/speaker-diarization-3.1 and accept the license

# std::bad_alloc crash
# Error: Application crashes with "std::bad_alloc" after matplotlib log
# Solution: Wrong pyannote.audio version installed (4.x instead of 3.3.2)
pip uninstall pyannote.audio matplotlib -y
pip install -r backend/requirements.txt

# First-time model download
# The first diarization will take longer (~300MB model download)
# Subsequent requests will be faster
```

## Container Deployment

EchoNote can be deployed using Podman with Red Hat Universal Base Image (UBI).

### Quick Container Deployment

```bash
# Build all 5 images (backend, frontend, Redis, Celery worker, Celery beat)
podman build -t localhost/echonote-backend:latest backend/
podman build -t localhost/echonote-frontend:latest frontend/
podman build -t localhost/echonote-redis:latest -f redis/Containerfile redis/
podman build -t localhost/echonote-celery:latest -f backend/Containerfile.celery backend/
podman build -t localhost/echonote-celery-beat:latest -f backend/Containerfile.celery-beat backend/

# Edit configuration
vi echonote-kube-priv.yaml  # Update MODEL_URL, HF_TOKEN, and other settings

# Deploy with Podman
podman kube play echonote-kube-priv.yaml

# Check status
podman pod ps
podman ps

# Verify services are ready
podman logs echonote-backend          # Should see "Uvicorn running"
podman logs echonote-celery-worker    # Should see "celery@echonote ready"
podman logs echonote-celery-beat      # Should see "beat: Starting..."
podman exec echonote-redis redis-cli ping  # Should return "PONG"

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
```

**Important:** EchoNote requires all 5 containers (Backend, Frontend, Redis, Celery Worker, Celery Beat) to function. The legacy `echonote-kube.yaml` file (2 containers only) is no longer functional as the backend now requires Celery for transcription processing and Celery Beat for scheduled tasks (quota reset).

### Container Files

- **`backend/Containerfile`** - Backend multi-stage build using UBI 10 Python 3.12 minimal
- **`backend/Containerfile.celery`** - Celery worker container build (full dependencies)
- **`backend/Containerfile.celery-beat`** - Celery Beat scheduler container build (minimal dependencies)
- **`backend/.containerignore`** - Backend container build exclusions
- **`backend/requirements.txt`** - Python dependencies (full - includes Celery 5.5.3, audio/ML libs)
- **`backend/requirements-beat.txt`** - Minimal dependencies for Beat scheduler (no audio/ML libs)
- **`frontend/Containerfile`** - Frontend build using UBI 10 Node.js 22 with `serve`
- **`frontend/.containerignore`** - Frontend container build exclusions
- **`frontend/.gitignore`** - Frontend git exclusions
- **`redis/Containerfile`** - Redis 7 container build
- **`redis/redis.conf`** - Custom Redis configuration (persistence disabled)
- **`echonote-kube-priv.yaml`** - Kubernetes YAML for full 5-container deployment (REQUIRED)
- **`echonote-kube.yaml`** - Legacy 2-container deployment (NOT FUNCTIONAL)
- **`CONTAINER.md`** - Comprehensive container deployment guide
- **`CELERY_ARCHITECTURE.md`** - Celery Beat/Worker separation architecture documentation

### Features

✅ Red Hat UBI 10 base images
✅ Backend uses multi-stage build for minimal size
✅ Both containers run as non-root user (UID 1001)
✅ Health checks and probes on both containers
✅ Lightweight Node.js static file server for frontend
✅ Systemd integration support
✅ Compatible with Kubernetes/OpenShift

For detailed container deployment instructions, see [CONTAINER.md](CONTAINER.md).

## OpenShift Deployment

EchoNote can be deployed to OpenShift 4.19 with PostgreSQL 16 and images hosted on Quay.io.

### Prerequisites

- OpenShift 4.19 cluster access
- `oc` CLI tool installed and configured
- Quay.io account for storing container images
- PostgreSQL 16 support (rhel10/postgresql-16)

### Quick OpenShift Deployment

```bash
# 1. Build and push images to Quay.io
podman login quay.io
podman build -t quay.io/YOUR_USERNAME/echonote-backend:latest backend/
podman push quay.io/YOUR_USERNAME/echonote-backend:latest

podman build -t quay.io/YOUR_USERNAME/echonote-frontend:latest frontend/
podman push quay.io/YOUR_USERNAME/echonote-frontend:latest

# 2. Update the deployment file with your Quay.io username
sed -i 's/pgustafs/YOUR_USERNAME/g' openshift-deployment.yaml

# 3. Update PostgreSQL password (IMPORTANT: Change in production!)
# Edit openshift-deployment.yaml and update the postgresql-secret password

# 4. Deploy to OpenShift (initial deployment)
oc apply -f openshift-deployment.yaml

# 5. Get your OpenShift route URLs
# These are auto-generated URLs that OpenShift creates for external access
oc get routes -n echonote

# Example output:
# NAME       HOST/PORT                                          PATH   SERVICES   PORT   TERMINATION   WILDCARD
# backend    backend-echonote.apps.YOUR_CLUSTER.example.com            backend    http   edge          None
# frontend   frontend-echonote.apps.YOUR_CLUSTER.example.com           frontend   http   edge          None

# Get URLs directly:
echo "Frontend URL: https://$(oc get route frontend -n echonote -o jsonpath='{.spec.host}')"
echo "Backend URL: https://$(oc get route backend -n echonote -o jsonpath='{.spec.host}')"

# 6. Update CORS origins with your actual route URLs
# Edit openshift-deployment.yaml ConfigMap section:
# Find the CORS_ORIGINS line and update it with your route URLs from step 5
# CORS_ORIGINS: "https://frontend-echonote.apps.YOUR_CLUSTER.example.com,https://backend-echonote.apps.YOUR_CLUSTER.example.com"

# Apply the updated configuration
oc apply -f openshift-deployment.yaml

# Restart backend to pick up new CORS settings
oc rollout restart deployment/backend -n echonote

# 7. Initialize the database (run once)
# Wait for all pods to be ready
oc get pods -n echonote -w

# Run database migration
oc exec -n echonote deployment/backend -- alembic upgrade head

# 8. Access the application
# Open the frontend URL from step 5 in your browser
# Example: https://frontend-echonote.apps.YOUR_CLUSTER.example.com
```

### Understanding OpenShift Routes

OpenShift automatically creates publicly accessible URLs for your services through Routes. Here's how to work with them:

```bash
# List all routes in the echonote namespace
oc get routes -n echonote

# Get detailed route information
oc describe route frontend -n echonote
oc describe route backend -n echonote

# Get just the hostname for frontend
oc get route frontend -n echonote -o jsonpath='{.spec.host}'
# Output example: frontend-echonote.apps.cluster.example.com

# Get the full URL with https://
echo "https://$(oc get route frontend -n echonote -o jsonpath='{.spec.host}')"

# Get both URLs in one command
echo "Frontend: https://$(oc get route frontend -n echonote -o jsonpath='{.spec.host}')"
echo "Backend: https://$(oc get route backend -n echonote -o jsonpath='{.spec.host}')"

# Save to environment variables for easy reuse
export FRONTEND_URL="https://$(oc get route frontend -n echonote -o jsonpath='{.spec.host}')"
export BACKEND_URL="https://$(oc get route backend -n echonote -o jsonpath='{.spec.host}')"

# Test the routes
curl -I $FRONTEND_URL
curl $BACKEND_URL
```

The route URLs follow this pattern:
- Format: `<route-name>-<namespace>.apps.<cluster-domain>`
- Example: `frontend-echonote.apps.ai3.pgustafs.com`
- Always use `https://` (TLS is enabled by default)

### OpenShift Deployment Architecture

The OpenShift deployment includes:

**PostgreSQL 16 Database:**
- Image: `registry.redhat.io/rhel10/postgresql-16:latest`
- 10Gi persistent storage
- Credentials stored in Secrets
- Health checks and automatic restarts

**Backend Service:**
- Image: `quay.io/YOUR_USERNAME/echonote-backend:latest`
- PostgreSQL database connection
- Whisper transcription models (whisper-large-v3-turbo-quantizedw4a16, kb-whisper-large)
- AI assistant models (gpt-4o, claude-3-5-sonnet)
- HuggingFace cache (2Gi persistent storage for pyannote diarization models)
- JWT authentication with secure secrets
- TLS-enabled Route for external access
- Resource limits: 2 CPU, 28Gi RAM

**Frontend Service:**
- Image: `quay.io/YOUR_USERNAME/echonote-frontend:latest`
- Static file serving with Node.js
- TLS-enabled Route for external access
- Resource limits: 500m CPU, 256Mi RAM

**Security Features:**
- Secrets for PostgreSQL credentials, JWT secret, and HuggingFace token
- Non-root containers with dropped capabilities
- SeccompProfile and proper security contexts
- TLS termination at edge with redirect for insecure traffic
- Network policies for pod-to-pod communication

### Configuration

The deployment uses three main configuration resources:

**Secrets** (sensitive data):
- `postgresql-secret`: Database credentials
- `jwt-secret`: JWT signing key (change in production!)
- `huggingface-secret`: HuggingFace API token for diarization models

**ConfigMap** (application settings):
- Whisper models configuration
- AI assistant models (GPT-4o, Claude 3.5 Sonnet)
- CORS origins (must match your OpenShift route URLs)
- JWT algorithm and token expiration
- Diarization model settings

**PersistentVolumeClaims** (storage):
- `postgresql-data`: 10Gi for PostgreSQL database
- `huggingface-cache`: 2Gi for pyannote diarization models (prevents re-downloading ~300MB model on restarts)

### Updating the Deployment

```bash
# Update container images
podman build -t quay.io/YOUR_USERNAME/echonote-backend:latest backend/
podman push quay.io/YOUR_USERNAME/echonote-backend:latest

# Trigger rolling update
oc rollout restart deployment/backend -n echonote
oc rollout status deployment/backend -n echonote

# Update frontend
podman build -t quay.io/YOUR_USERNAME/echonote-frontend:latest frontend/
podman push quay.io/YOUR_USERNAME/echonote-frontend:latest
oc rollout restart deployment/frontend -n echonote
```

### Monitoring and Logs

```bash
# View pod logs
oc logs -f deployment/backend -n echonote
oc logs -f deployment/frontend -n echonote
oc logs -f deployment/postgresql -n echonote

# Check pod status
oc get pods -n echonote
oc describe pod backend-XXXXX -n echonote

# View events
oc get events -n echonote --sort-by='.lastTimestamp'

# Check routes and their status
oc get routes -n echonote
oc describe route frontend -n echonote
```

### Scaling

```bash
# Scale backend (if needed for high load)
oc scale deployment/backend --replicas=3 -n echonote

# Scale frontend
oc scale deployment/frontend --replicas=2 -n echonote

# Note: PostgreSQL should remain at 1 replica (single primary)
```

### Troubleshooting OpenShift Deployment

**Pod not starting:**
```bash
# Check pod events
oc describe pod POD_NAME -n echonote

# Check image pull
oc get events -n echonote | grep -i pull

# Verify Quay.io credentials (images should be public or you need imagePullSecrets)
oc get pods -n echonote
```

**Database connection issues:**
```bash
# Test PostgreSQL connectivity
oc exec -it deployment/backend -n echonote -- env | grep DATABASE
oc exec -it deployment/postgresql -n echonote -- psql -U echonote -d echonote -c 'SELECT 1'

# Check PostgreSQL logs
oc logs deployment/postgresql -n echonote
```

**Route not accessible:**
```bash
# Check route configuration
oc get route frontend -n echonote -o yaml
oc get route backend -n echonote -o yaml

# Verify TLS termination
curl -I https://$(oc get route frontend -n echonote -o jsonpath='{.spec.host}')

# Test backend health
curl https://$(oc get route backend -n echonote -o jsonpath='{.spec.host}')
```

**CORS errors in browser console:**
```bash
# This means CORS_ORIGINS doesn't match your actual route URLs
# Get your route URLs
oc get routes -n echonote

# Update CORS_ORIGINS in openshift-deployment.yaml with the exact URLs
# Then apply and restart:
oc apply -f openshift-deployment.yaml
oc rollout restart deployment/backend -n echonote
```

**HuggingFace model download issues:**
```bash
# Check HF token
oc exec deployment/backend -n echonote -- env | grep HF_TOKEN

# Check cache volume
oc exec deployment/backend -n echonote -- ls -la /opt/app-root/src/hf-cache

# Monitor first diarization request (downloads ~300MB)
oc logs -f deployment/backend -n echonote
```

### Database Migrations

```bash
# Create a new migration
oc exec -it deployment/backend -n echonote -- alembic revision --autogenerate -m "description"

# Apply migrations
oc exec -it deployment/backend -n echonote -- alembic upgrade head

# View migration history
oc exec -it deployment/backend -n echonote -- alembic history

# Rollback migration
oc exec -it deployment/backend -n echonote -- alembic downgrade -1
```

### Production Checklist

Before deploying to production:

- [ ] Change PostgreSQL password in `postgresql-secret`
- [ ] Generate new JWT secret key: `openssl rand -hex 32`
- [ ] Update JWT_SECRET_KEY in `jwt-secret`
- [ ] Set your HuggingFace token in `huggingface-secret`
- [ ] Update Quay.io image references with your username
- [ ] Deploy first, then get route URLs: `oc get routes -n echonote`
- [ ] Update CORS_ORIGINS with your actual OpenShift route URLs
- [ ] Redeploy to apply CORS changes: `oc apply -f openshift-deployment.yaml && oc rollout restart deployment/backend -n echonote`
- [ ] Review resource limits (CPU/memory) based on your cluster capacity
- [ ] Set up backup strategy for PostgreSQL PVC
- [ ] Configure monitoring and alerting
- [ ] Test database migrations
- [ ] Verify TLS certificates on routes
- [ ] Test authentication flow
- [ ] Test transcription and diarization functionality

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

When contributing to the backend, please follow the established architecture:
- **API endpoints** go in `backend/routers/` (organized by domain)
- **Business logic** goes in `backend/services/`
- **Database models and schemas** go in `backend/models.py`
- Use type hints and comprehensive docstrings
- Follow the service layer pattern (keep routers thin)

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [SQLModel](https://sqlmodel.tiangolo.com/) - SQL databases with Python
- [Vite](https://vitejs.dev/) - Next generation frontend tooling
- [OpenAI Whisper](https://openai.com/research/whisper) - Speech recognition model
- [vLLM](https://github.com/vllm-project/vllm) - Fast LLM inference engine
- [pyannote.audio](https://github.com/pyannote/pyannote-audio) - Speaker diarization toolkit
