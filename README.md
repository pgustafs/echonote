# EchoNote 🎤

A modern, beautiful voice transcription application built with FastAPI and Vite. Record voice messages, transcribe them using Whisper (via vLLM), and store both the audio and transcriptions in a database.

## Features

✨ **Modern UI** - Beautiful, responsive interface built with React and Tailwind CSS with streamlined single-button control
🔐 **User Authentication** - Secure JWT-based authentication with user registration and login
🎙️ **Audio Recording** - Record directly in the browser with one-click start/stop using the microphone button
🤖 **AI Transcription** - Powered by Whisper (large-v3-turbo) via vLLM
👥 **Speaker Diarization** - Detect and separate different speakers using pyannote.audio (optional, CPU-only)
💾 **Persistent Storage** - Audio files and transcriptions stored in database with user ownership
🎵 **Audio Playback** - Listen to your recordings with built-in player
📥 **Download Package** - Download transcriptions as ZIP with WAV audio and config.json
🔍 **Search & Filter** - Full-text search in transcriptions with priority filtering
📱 **Responsive Design** - Works seamlessly on desktop and mobile with dedicated mobile layout
🌓 **Dark Mode Ready** - Beautiful UI in both light and dark themes
🎨 **Format Conversion** - Server-side WebM to WAV conversion with FFmpeg (isolated subprocess)
📴 **PWA Support** - Install as app, offline recording, background sync

## Tech Stack

### Backend
- **FastAPI** - Modern, fast web framework for building APIs
- **SQLModel** - SQL databases using Python type hints
- **SQLite** - Development database (auto-created)
- **PostgreSQL** - Production database support
- **PyJWT** - JWT token generation and validation
- **Passlib** - Password hashing with bcrypt
- **OpenAI SDK** - For Whisper API calls to vLLM server
- **pyannote.audio** - Speaker diarization (CPU-only PyTorch)

### Frontend
- **Vite** - Next generation frontend tooling
- **React 18** - UI library with hooks
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **MediaRecorder API** - Browser-native audio recording

## Project Structure

```
echonote/
├── backend/
│   ├── Containerfile       # Backend container build (UBI 10 Python)
│   ├── .containerignore    # Backend build exclusions
│   ├── requirements.txt    # Python dependencies
│   ├── __init__.py
│   ├── main.py             # FastAPI application
│   ├── models.py           # SQLModel database models (User, Transcription)
│   ├── database.py         # Database configuration
│   ├── config.py           # Application settings
│   ├── auth.py             # Authentication utilities (JWT, password hashing)
│   └── auth_routes.py      # Authentication endpoints (register, login)
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
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── api.ts          # API client with JWT token support
│   │   ├── types.ts        # TypeScript types
│   │   └── index.css
│   ├── index.html
│   ├── vite.config.ts
│   └── tailwind.config.js
├── echonote-kube.yaml      # Kubernetes/Podman deployment
├── .gitignore              # Project-level git ignores
├── CONTAINER.md            # Container deployment guide
├── .env.example
└── README.md
```

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
# Build both images
podman build -t localhost/echonote-backend:latest backend/
podman build -t localhost/echonote-frontend:latest frontend/

# Edit configuration
vi echonote-kube.yaml  # Update MODEL_URL and other settings

# Deploy with Podman
podman kube play echonote-kube.yaml

# Check status
podman pod ps
podman ps

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
```

### Container Files

- **`backend/Containerfile`** - Backend multi-stage build using UBI 10 Python 3.12 minimal
- **`backend/.containerignore`** - Backend container build exclusions
- **`backend/requirements.txt`** - Python dependencies
- **`frontend/Containerfile`** - Frontend build using UBI 10 Node.js 22 with `serve`
- **`frontend/.containerignore`** - Frontend container build exclusions
- **`frontend/.gitignore`** - Frontend git exclusions
- **`echonote-kube.yaml`** - Kubernetes YAML for `podman kube play` (both frontend and backend)
- **`CONTAINER.md`** - Comprehensive container deployment guide

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

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [SQLModel](https://sqlmodel.tiangolo.com/) - SQL databases with Python
- [Vite](https://vitejs.dev/) - Next generation frontend tooling
- [OpenAI Whisper](https://openai.com/research/whisper) - Speech recognition model
- [vLLM](https://github.com/vllm-project/vllm) - Fast LLM inference engine
- [pyannote.audio](https://github.com/pyannote/pyannote-audio) - Speaker diarization toolkit
