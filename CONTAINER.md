# EchoNote Container Deployment Guide

This guide covers building and deploying EchoNote using containers with Red Hat UBI images and Podman.

## Deployment Options

EchoNote requires a **5-container deployment** for full functionality:

### Production Deployment (5 containers) - REQUIRED
- **Frontend** - React/Vite SPA
- **Backend** - FastAPI REST API
- **Redis** - Message broker and result backend
- **Celery Worker** - Async transcription processor
- **Celery Beat** - Scheduled task scheduler (daily quota reset)
- **Use case**: All environments (development, testing, production)
- **File**: `echonote-kube-priv.yaml`

**Note:** The application currently requires Celery and Redis for transcription processing. There is no synchronous fallback mode. All transcriptions are processed as background tasks. Celery Beat is required for scheduled tasks like daily quota resets.

## Quick Start

```bash
# 1. Build all images
podman build -t localhost/echonote-backend:latest backend/
podman build -t localhost/echonote-frontend:latest frontend/
podman build -t localhost/echonote-redis:latest -f redis/Containerfile redis/
podman build -t localhost/echonote-celery:latest -f backend/Containerfile.celery backend/
podman build -t localhost/echonote-celery-beat:latest -f backend/Containerfile.celery-beat backend/

# 2. Edit configuration
vi echonote-kube-priv.yaml  # Update MODEL_URL, HF_TOKEN, and other settings

# 3. Deploy
podman kube play echonote-kube-priv.yaml

# 4. Check status
podman pod ps
podman ps

# 5. Verify services are ready
podman logs echonote-backend          # Should see "Uvicorn running"
podman logs echonote-celery-worker    # Should see "celery@echonote ready"
podman logs echonote-celery-beat      # Should see "beat: Starting..."
podman exec echonote-redis redis-cli ping  # Should return "PONG"

# 6. Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
```


## Prerequisites

- Podman installed (version 4.0 or later recommended)
- Access to Red Hat Container Registry (for UBI images)

## Architecture

EchoNote uses a 5-container architecture with async background processing and scheduled tasks:

#### Backend Container (`backend/Containerfile`)
- **Base Image**: UBI 10 Python 3.12 minimal
- **Build Context**: `backend/` directory
- **Multi-stage Build**: Builder stage installs dependencies, runtime stage is minimal
- **Port**: 8000
- **Purpose**: FastAPI REST API for transcription services
- **Storage**: Persistent volume for SQLite database and audio files
- **Dependencies**: `backend/requirements.txt`
- **Exclusions**: `backend/.containerignore`
- **Environment**: Connects to Redis for task queuing

#### Frontend Container (`frontend/Containerfile`)
- **Base Image**: UBI 10 Node.js 22
- **Build Context**: `frontend/` directory
- **Single-stage Build**: Builds the Vite app and serves with `serve` package
- **Port**: 8080 (mapped to host port 5173)
- **Purpose**: React/Vite SPA served by Node.js static file server
- **Dependencies**: `frontend/package.json`
- **Exclusions**: `frontend/.containerignore`
- **Note**: Uses `serve` for lightweight static file serving
- **Features**: Real-time polling for transcription status updates

#### Redis Container (`redis/Containerfile`)
- **Base Image**: UBI 9 with Redis 7
- **Build Context**: `redis/` directory
- **Configuration**: Custom `redis.conf` with RDB persistence disabled
- **Port**: 6379
- **Purpose**: Message broker (db 0) and result backend (db 1) for Celery
- **Memory**: 512MB max with allkeys-lru eviction policy
- **Health Check**: Redis CLI ping every 30s
- **Note**: Optimized for task queuing, not data persistence

#### Celery Worker Container (`backend/Containerfile.celery`)
- **Base Image**: UBI 10 Python 3.12 minimal
- **Build Context**: `backend/` directory
- **Multi-stage Build**: Same dependencies as backend
- **Purpose**: Async transcription processing worker
- **Worker**: Single worker process with concurrency 2
- **Log Level**: INFO
- **Environment**: Connects to Redis broker and result backend
- **Features**: Audio chunking, speaker diarization, progress tracking
- **Dependencies**: Full `requirements.txt` (includes Celery 5.5.3, audio/ML libraries)
- **Image Size**: ~2GB+ (includes PyTorch, ffmpeg, audio processing libraries)

#### Celery Beat Container (`backend/Containerfile.celery-beat`)
- **Base Image**: UBI 10 Python 3.12 minimal
- **Build Context**: `backend/` directory
- **Multi-stage Build**: Minimal dependencies for scheduler only
- **Purpose**: Scheduled task scheduler (sends tasks to queue at specified times)
- **Scheduled Tasks**: Daily quota reset at midnight UTC
- **Log Level**: INFO
- **Environment**: Connects to Redis broker and database
- **Dependencies**: Minimal `requirements-beat.txt` (Celery, Redis, FastAPI, SQLModel - NO audio/ML libs)
- **Image Size**: ~400MB (80% smaller than worker)
- **Architecture**: Proper Beat/Worker separation following official Celery best practices
- **Documentation**: See [CELERY_ARCHITECTURE.md](CELERY_ARCHITECTURE.md) for detailed architecture

**Key Difference - Beat vs Worker:**
- **Beat** = Scheduler (lightweight, only knows task **names** as strings)
- **Worker** = Executor (heavyweight, imports and runs actual task **code**)
- Beat sends "execute task named X" to Redis at scheduled times
- Worker picks up task from Redis and executes the Python function
- This separation allows minimal dependencies for Beat (no PyTorch, ffmpeg, etc.)

## Building the Containers

### Build All Images

```bash
# Build backend
podman build -t localhost/echonote-backend:latest backend/

# Build frontend
podman build -t localhost/echonote-frontend:latest frontend/

# Build Redis
podman build -t localhost/echonote-redis:latest -f redis/Containerfile redis/

# Build Celery worker
podman build -t localhost/echonote-celery:latest -f backend/Containerfile.celery backend/

# Build Celery beat scheduler
podman build -t localhost/echonote-celery-beat:latest -f backend/Containerfile.celery-beat backend/

# Or build all at once
podman build -t localhost/echonote-backend:latest backend/ && \
podman build -t localhost/echonote-frontend:latest frontend/ && \
podman build -t localhost/echonote-redis:latest -f redis/Containerfile redis/ && \
podman build -t localhost/echonote-celery:latest -f backend/Containerfile.celery backend/ && \
podman build -t localhost/echonote-celery-beat:latest -f backend/Containerfile.celery-beat backend/
```

## Running the Container

### Option 1: Using Podman Kube Play (Recommended)

This is the recommended approach as it uses standard Kubernetes YAML and works seamlessly with OpenShift and Kubernetes.

```bash
# 1. Build both images
podman build -t localhost/echonote-backend:latest backend/
podman build -t localhost/echonote-frontend:latest frontend/

# 2. Edit the configuration in echonote-kube-priv.yaml
# Update the ConfigMap section with your vLLM server URL and other settings

# 3. Deploy the application
podman kube play echonote-kube-priv.yaml

# 4. Verify pods are running
podman pod ps
podman ps

# 5. View logs
podman logs echonote-backend     # Backend logs
podman logs echonote-frontend    # Frontend logs
```

To customize configuration before deploying, edit the ConfigMap in `echonote-kube-priv.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: echonote-config
data:
  MODEL_URL: "http://your-vllm-server:8080/v1"  # Change this
  MODEL_NAME: "whisper"
  API_KEY: "your-api-key"  # Change if needed
  CORS_ORIGINS: "http://localhost:5173,https://your-frontend.com"
```

#### Managing the Deployment

```bash
# Stop the deployment
podman kube down echonote-kube-priv.yaml

# Restart after configuration changes
podman kube down echonote-kube-priv.yaml
podman kube play echonote-kube-priv.yaml

# View all resources
podman pod ps
podman ps -a

# Check logs
podman logs -f echonote-backend-backend
```

### Option 2: Using Podman Run (Simple Testing)

For quick testing without Kubernetes YAML:

```bash
# Create a volume for data persistence
podman volume create echonote-data

# Run the container
podman run -d \
  --name echonote-backend \
  -p 8000:8000 \
  -e MODEL_URL=http://your-vllm-server:8080/v1 \
  -e MODEL_NAME=whisper \
  -e API_KEY=not-needed \
  -e CORS_ORIGINS=http://localhost:5173 \
  -v echonote-data:/opt/app-root/src/data:Z \
  localhost/echonote-backend:latest
```

### Option 3: Deploy to OpenShift/Kubernetes

The `echonote-kube-priv.yaml` file is compatible with standard Kubernetes and OpenShift:

```bash
# For Kubernetes
kubectl apply -f echonote-kube-priv.yaml

# For OpenShift
oc apply -f echonote-kube-priv.yaml

# Check deployment status
kubectl get pods
kubectl logs -f echonote-backend

# Or for OpenShift
oc get pods
oc logs -f echonote-backend
```

## Environment Variables

### Backend and Celery Worker

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MODEL_URL` | vLLM Whisper server URL | `http://localhost:8080/v1` | Yes |
| `MODEL_NAME` | Model name to use | `whisper` | Yes |
| `API_KEY` | API key for Whisper server | `not-needed` | No |
| `DATABASE_URL` | PostgreSQL connection URL | (uses SQLite if not set) | No |
| `SQLITE_DB` | SQLite database path | `/opt/app-root/src/data/echonote.db` | No |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:5173` | Yes |
| `MAX_UPLOAD_SIZE` | Max file upload size in bytes | `104857600` (100MB) | No |
| `CELERY_BROKER_URL` | Redis broker URL (full deployment) | `redis://localhost:6379/0` | Yes (full) |
| `CELERY_RESULT_BACKEND` | Redis result backend URL (full deployment) | `redis://localhost:6379/1` | Yes (full) |
| `HF_TOKEN` | Hugging Face token for pyannote models | - | No |
| `CHUNK_LENGTH_MS` | Audio chunk length for processing | `30000` (30s) | No |
| `ENABLE_DIARIZATION` | Enable speaker diarization | `false` | No |
| `JWT_SECRET_KEY` | JWT signing secret | - | Yes |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` | No |
| `ACCESS_TOKEN_EXPIRE_DAYS` | JWT token expiration in days | `30` | No |

### Celery Beat

Celery Beat requires minimal environment variables (does not execute tasks, only schedules them):

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SQLITE_DB` | SQLite database path (for quota reset task) | `/opt/app-root/src/data/echonote.db` | Yes |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` | Yes |
| `CELERY_BROKER_URL` | Redis broker URL | `redis://localhost:6379/0` | Yes |
| `CELERY_RESULT_BACKEND` | Redis result backend URL | `redis://localhost:6379/1` | Yes |
| `JWT_SECRET_KEY` | JWT signing secret (for config validation) | - | Yes |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` | No |

**Note:** Beat does NOT need:
- `MODEL_URL`, `API_KEY` (no transcription)
- `HF_TOKEN` (no diarization)
- `CORS_ORIGINS` (no HTTP server)
- Audio processing environment variables

### Redis

Redis configuration is set in `redis/redis.conf`:
- **Port**: 6379
- **Max Memory**: 512MB
- **Eviction Policy**: allkeys-lru
- **Persistence**: Disabled (snapshots turned off)
- **Database 0**: Celery message broker
- **Database 1**: Celery result backend

## Using Podman Secrets (Best Practice)

For sensitive data like API keys and database passwords, use Podman secrets instead of ConfigMaps:

```bash
# Create secrets
echo -n "your-api-key" | podman secret create whisper-api-key -
echo -n "postgresql://user:pass@host/db" | podman secret create database-url -

# Create a modified Kubernetes YAML that uses secrets
# echonote-kube-secrets.yaml
```

Example YAML with secrets:

```yaml
---
apiVersion: v1
kind: Pod
metadata:
  name: echonote-backend
spec:
  containers:
  - name: backend
    image: localhost/echonote-backend:latest
    env:
    - name: API_KEY
      valueFrom:
        secretKeyRef:
          name: whisper-api-key
    - name: DATABASE_URL
      valueFrom:
        secretKeyRef:
          name: database-url
    # ... rest of config
```

Note: As of Podman 4.x, secret support in `podman kube play` may be limited. Check your Podman version:
```bash
podman version
```

For older versions, use environment variables or mount secrets as files.

## Using PostgreSQL Instead of SQLite

To use PostgreSQL instead of SQLite, you need to:

1. Deploy a PostgreSQL pod
2. Update the ConfigMap to include `DATABASE_URL`

### Deploy PostgreSQL

Create a file `postgres-kube.yaml`:

```yaml
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi

---
apiVersion: v1
kind: Pod
metadata:
  name: echonote-postgres
  labels:
    app: echonote-postgres
spec:
  restartPolicy: Always
  containers:
  - name: postgres
    image: registry.redhat.io/rhel9/postgresql-15:latest
    ports:
    - containerPort: 5432
      protocol: TCP
    env:
    - name: POSTGRESQL_USER
      value: "echonote"
    - name: POSTGRESQL_PASSWORD
      value: "changeme"
    - name: POSTGRESQL_DATABASE
      value: "echonote"
    volumeMounts:
    - name: postgres-data
      mountPath: /var/lib/pgsql/data
    resources:
      limits:
        cpu: "1"
        memory: "1Gi"
      requests:
        cpu: "250m"
        memory: "256Mi"
  volumes:
  - name: postgres-data
    persistentVolumeClaim:
      claimName: postgres-data
```

Deploy it:

```bash
podman kube play postgres-kube.yaml
```

### Update EchoNote Configuration

Edit `echonote-kube-priv.yaml` and add `DATABASE_URL` to the ConfigMap:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: echonote-config
data:
  DATABASE_URL: "postgresql://echonote:changeme@echonote-postgres:5432/echonote"
  MODEL_URL: "http://localhost:8080/v1"
  # ... other config
```

Then update the backend pod's env section to include:

```yaml
    - name: DATABASE_URL
      valueFrom:
        configMapKeyRef:
          name: echonote-config
          key: DATABASE_URL
```

Redeploy:

```bash
podman kube down echonote-kube-priv.yaml
podman kube play echonote-kube-priv.yaml
```

## Health Checks

The container includes built-in health checks (liveness and readiness probes) that verify the API is responding:

```bash
# Check pod and container status
podman pod ps
podman ps

# For detailed health check status
podman inspect echonote-backend-backend | grep -A 10 Health
```

Look for the `STATUS` column showing `healthy` or `Up` status.

## Logs

```bash
# View backend API logs
podman logs -f echonote-backend

# View frontend logs
podman logs -f echonote-frontend

# View Redis logs
podman logs -f echonote-redis

# View Celery worker logs (most important for debugging transcriptions)
podman logs -f echonote-celery-worker

# View Celery beat scheduler logs (for scheduled tasks)
podman logs -f echonote-celery-beat

# Follow all logs in real-time
podman logs -f echonote-backend &
podman logs -f echonote-celery-worker &
podman logs -f echonote-celery-beat &

# View pod logs (all containers)
podman pod logs echonote
```

### Monitoring Celery Tasks

**Check Beat Scheduler:**
```bash
# Verify beat is running and sending scheduled tasks
podman logs echonote-celery-beat 2>&1 | grep "beat: Starting"
# Should show: [INFO/MainProcess] beat: Starting...

# Check beat schedule configuration
podman logs echonote-celery-beat 2>&1 | grep "reset-daily-quotas"
# Note: Schedule only shows at DEBUG level, not INFO

# Manually trigger scheduled task for testing (from worker container)
podman exec echonote-celery-worker celery -A backend.celery_app call reset_daily_quotas
```

**Check Celery Worker:**

```bash
# Check Celery worker status
podman exec echonote-celery-worker celery -A celery_app inspect active

# Check registered tasks
podman exec echonote-celery-worker celery -A celery_app inspect registered

# Check worker stats
podman exec echonote-celery-worker celery -A celery_app inspect stats

# Monitor Redis queue length
podman exec echonote-redis redis-cli -n 0 llen celery

# Check task results in Redis
podman exec echonote-redis redis-cli -n 1 keys "celery-task-meta-*"
```

## Security Best Practices

1. **Non-root user**: Container runs as user 1001 (non-root)
2. **Read-only filesystem**: Consider mounting the root filesystem as read-only:
   ```bash
   podman run --read-only -v echonote-data:/opt/app-root/src/data:Z ...
   ```
3. **Resource limits**: Always set CPU/memory limits in production
4. **Secrets management**: Use Kubernetes secrets or Podman secrets for sensitive data
5. **Network isolation**: Use custom networks to isolate containers

## Troubleshooting

### Pod won't start

Check pod and container status:
```bash
# View pod status
podman pod ps

# View container status
podman ps -a

# Check logs
podman logs echonote-backend-backend

# Inspect pod events
podman pod inspect echonote-backend
```

### Configuration not applied

After editing `echonote-kube-priv.yaml`, you must restart:
```bash
podman kube down echonote-kube-priv.yaml
podman kube play echonote-kube-priv.yaml
```

### Permission denied errors

Ensure volumes have correct SELinux labels. Podman kube play should handle this automatically, but if you use `podman run`, add `:Z` flag:
```bash
-v echonote-data:/opt/app-root/src/data:Z
```

### Can't connect to Whisper server

1. Verify the `MODEL_URL` in ConfigMap is correct
2. Ensure the Whisper server is accessible from the pod

For testing connectivity:
```bash
# Enter the container
podman exec -it echonote-backend /bin/sh

# Test connection (if curl is available)
curl http://your-whisper-server:8080/v1/models
```

If running locally, use host.containers.internal:
```yaml
MODEL_URL: "http://host.containers.internal:8080/v1"
```

### Celery worker not processing tasks

Check the worker logs and Redis connection:

```bash
# View Celery worker logs
podman logs -f echonote-celery-worker

# Check if worker is registered and active
podman exec echonote-celery-worker celery -A celery_app inspect active

# Verify Redis connectivity from worker
podman exec echonote-celery-worker redis-cli -h echonote-redis ping

# Check Redis broker database (db 0)
podman exec echonote-redis redis-cli -n 0 info
```

Common issues:
1. **Worker can't connect to Redis**: Ensure `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` point to the correct Redis host
2. **Tasks not appearing**: Check backend logs to verify tasks are being submitted
3. **Worker crashes**: Check for out-of-memory issues, increase worker memory limits

### Transcriptions stuck in "pending" or "processing"

This usually indicates the Celery worker is not processing tasks:

```bash
# Check worker status
podman logs echonote-celery-worker | tail -20

# Look for errors like:
# - "Event loop is closed" (fixed in current version)
# - Connection errors to Redis
# - Out of memory errors
# - Model URL connection failures

# Check task queue
podman exec echonote-redis redis-cli -n 0 llen celery

# If queue length is > 0, tasks are waiting but not being processed
# Restart the worker:
podman restart echonote-celery-worker
```

### Redis persistence errors

If you see errors like `Failed saving the DB: Permission denied`:

```bash
# This is expected and safe - we've disabled RDB persistence in redis.conf
# Redis is configured for task queuing only, not data persistence
# Check redis/redis.conf to verify "save ''" is set
```

### UI not showing real-time updates

The frontend polls for status every 2 seconds. If updates aren't showing:

```bash
# 1. Check browser console for errors
# 2. Verify backend /api/v1/transcriptions/status/bulk endpoint is working:
curl http://localhost:8000/api/v1/transcriptions/status/bulk?ids=1,2,3

# 3. Check backend logs for status update queries
podman logs echonote-backend | grep "status/bulk"

# 4. Ensure transcriptions have status fields in database
# (Fixed in current version - list_transcriptions endpoint returns status fields)
```

### Image pull issues

If you get authentication errors pulling UBI images:
```bash
podman login registry.access.redhat.com
# Enter your Red Hat account credentials
```

### Generate Kubernetes YAML from running pod

If you want to generate YAML from a running deployment:
```bash
podman kube generate echonote-backend > my-echonote-kube-priv.yaml
```

## Systemd Integration (Auto-start on Boot)

Podman can generate systemd unit files for automatic startup:

```bash
# Deploy with podman kube play first
podman kube play echonote-kube-priv.yaml

# Generate systemd service files
podman kube generate systemd echonote-backend \
  --new \
  --files \
  --name

# For user services (rootless)
mkdir -p ~/.config/systemd/user/
mv pod-echonote-backend.service ~/.config/systemd/user/

# Enable and start the service
systemctl --user daemon-reload
systemctl --user enable pod-echonote-backend.service
systemctl --user start pod-echonote-backend.service

# Check status
systemctl --user status pod-echonote-backend.service

# Enable linger (keeps user services running after logout)
loginctl enable-linger $USER
```

For system-wide services (requires root):
```bash
sudo mv pod-echonote-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pod-echonote-backend.service
sudo systemctl start pod-echonote-backend.service
```

## Building for Different Architectures

```bash
# Build backend for AMD64
podman build --platform linux/amd64 -t localhost/echonote-backend:amd64 backend/

# Build backend for ARM64
podman build --platform linux/arm64 -t localhost/echonote-backend:arm64 backend/

# Build frontend for AMD64
podman build --platform linux/amd64 -t localhost/echonote-frontend:amd64 frontend/

# Build frontend for ARM64
podman build --platform linux/arm64 -t localhost/echonote-frontend:arm64 frontend/

# Create manifests for multi-arch
podman manifest create localhost/echonote-backend:latest
podman manifest add localhost/echonote-backend:latest localhost/echonote-backend:amd64
podman manifest add localhost/echonote-backend:latest localhost/echonote-backend:arm64

podman manifest create localhost/echonote-frontend:latest
podman manifest add localhost/echonote-frontend:latest localhost/echonote-frontend:amd64
podman manifest add localhost/echonote-frontend:latest localhost/echonote-frontend:arm64
```

## Production Deployment Checklist

### Security
- [ ] Update ConfigMap with production values (remove defaults)
- [ ] Use Kubernetes/Podman secrets for sensitive data (API keys, passwords)
- [ ] Set strong passwords for PostgreSQL
- [ ] Configure proper CORS origins (not `*`)
- [ ] Review and apply security contexts
- [ ] Enable SELinux (enforcing mode)
- [ ] Use rootless Podman when possible

### Configuration
- [ ] Set appropriate resource limits (CPU/memory) in YAML
- [ ] Configure proper persistent volume sizes
- [ ] Set up systemd service for auto-start
- [ ] Enable lingering for rootless deployments
- [ ] Configure proper network policies

### Monitoring & Reliability
- [ ] Verify health checks are working
- [ ] Configure log aggregation (journald, syslog, or external)
- [ ] Set up monitoring and alerts
- [ ] Test pod restart behavior
- [ ] Verify backup strategy for database

### Networking
- [ ] Configure firewall rules (firewalld)
- [ ] Ensure Whisper server connectivity
- [ ] Set up reverse proxy (nginx/haproxy) with TLS
- [ ] Configure proper DNS resolution

### Maintenance
- [ ] Document deployment procedure
- [ ] Create backup/restore procedures
- [ ] Plan update strategy (rolling updates)
- [ ] Schedule regular security updates for UBI images
