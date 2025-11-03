# EchoNote 🎤

A modern, beautiful voice transcription application built with FastAPI and Vite. Record voice messages, transcribe them using Whisper (via vLLM), and store both the audio and transcriptions in a database.

## Features

✨ **Modern UI** - Beautiful, responsive interface built with React and Tailwind CSS
🎙️ **Audio Recording** - Record directly in the browser with pause/resume support
🤖 **AI Transcription** - Powered by Whisper (large-v3-turbo) via vLLM
💾 **Persistent Storage** - Audio files and transcriptions stored in database
🎵 **Audio Playback** - Listen to your recordings with built-in player
📱 **Responsive Design** - Works seamlessly on desktop and mobile
🌓 **Dark Mode Ready** - Beautiful UI in both light and dark themes
🎨 **Browser-Side Conversion** - WebM to WAV conversion happens in the browser (no FFmpeg needed!)

## Tech Stack

### Backend
- **FastAPI** - Modern, fast web framework for building APIs
- **SQLModel** - SQL databases using Python type hints
- **SQLite** - Development database (auto-created)
- **PostgreSQL** - Production database support
- **OpenAI SDK** - For Whisper API calls to vLLM server

### Frontend
- **Vite** - Next generation frontend tooling
- **React 18** - UI library with hooks
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **Web Audio API** - Browser-native audio processing for format conversion

## Project Structure

```
echonote/
├── backend/
│   ├── Containerfile       # Backend container build (UBI 10 Python)
│   ├── .containerignore    # Backend build exclusions
│   ├── requirements.txt    # Python dependencies
│   ├── __init__.py
│   ├── main.py             # FastAPI application
│   ├── models.py           # SQLModel database models
│   ├── database.py         # Database configuration
│   └── config.py           # Application settings
├── frontend/
│   ├── Containerfile       # Frontend container build (UBI 10 Node.js)
│   ├── .containerignore    # Frontend build exclusions
│   ├── .gitignore          # Frontend git ignores
│   ├── package.json
│   ├── src/
│   │   ├── components/
│   │   │   ├── AudioRecorder.tsx
│   │   │   └── TranscriptionList.tsx
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── api.ts          # API client
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

**Note:** Audio format conversion (WebM to WAV) is handled in the browser using the Web Audio API, so no additional dependencies like FFmpeg are needed!

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

- `POST /api/transcribe` - Upload and transcribe audio file
- `GET /api/transcriptions` - List all transcriptions (paginated)
- `GET /api/transcriptions/{id}` - Get specific transcription
- `GET /api/transcriptions/{id}/audio` - Download audio file
- `DELETE /api/transcriptions/{id}` - Delete transcription

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

1. **Record a voice message**:
   - Click "Start Recording"
   - Speak your message
   - Use "Pause" if needed
   - Click "Stop & Transcribe"

2. **View transcriptions**:
   - All transcriptions appear in the list below
   - Click on any transcription to expand it
   - View full text and play audio
   - Delete unwanted transcriptions

3. **Play audio**:
   - Expand a transcription
   - Click the play button or use the audio controls

## Troubleshooting

### Audio Format Conversion
Audio is converted from WebM to WAV format **in the browser** using the Web Audio API before being sent to the backend. If you see conversion errors in the browser console:
- Check that your browser supports the Web Audio API (all modern browsers do)
- Ensure the recording completed successfully
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
