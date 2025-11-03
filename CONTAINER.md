# EchoNote Container Deployment Guide

This guide covers building and deploying the EchoNote backend using containers with Red Hat UBI images and Podman.

## Quick Start

```bash
# 1. Build the image
podman build -t localhost/echonote-backend:latest -f Containerfile .

# 2. Edit configuration
vi echonote-kube.yaml  # Update MODEL_URL and other settings

# 3. Deploy
podman kube play echonote-kube.yaml

# 4. Check status
podman pod ps
podman logs -f echonote-backend-backend

# 5. Access the API
curl http://localhost:8000/
```

## Prerequisites

- Podman installed (version 4.0 or later recommended)
- Access to Red Hat Container Registry (for UBI images)

## Building the Container

```bash
# Build the container image
podman build -t localhost/echonote-backend:latest -f Containerfile .

# Or with specific version tag
podman build -t localhost/echonote-backend:1.0.0 -f Containerfile .
```

## Running the Container

### Option 1: Using Podman Kube Play (Recommended)

This is the recommended approach as it uses standard Kubernetes YAML and works seamlessly with OpenShift and Kubernetes.

```bash
# 1. Edit the configuration in echonote-kube.yaml
# Update the ConfigMap section with your vLLM server URL and other settings

# 2. Deploy the application
podman kube play echonote-kube.yaml

# 3. Verify the pod is running
podman pod ps
podman ps

# 4. View logs
podman logs echonote-backend-backend
```

To customize configuration before deploying, edit the ConfigMap in `echonote-kube.yaml`:

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
podman kube down echonote-kube.yaml

# Restart after configuration changes
podman kube down echonote-kube.yaml
podman kube play echonote-kube.yaml

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

The `echonote-kube.yaml` file is compatible with standard Kubernetes and OpenShift:

```bash
# For Kubernetes
kubectl apply -f echonote-kube.yaml

# For OpenShift
oc apply -f echonote-kube.yaml

# Check deployment status
kubectl get pods
kubectl logs -f echonote-backend

# Or for OpenShift
oc get pods
oc logs -f echonote-backend
```

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MODEL_URL` | vLLM Whisper server URL | `http://localhost:8080/v1` | Yes |
| `MODEL_NAME` | Model name to use | `whisper` | Yes |
| `API_KEY` | API key for Whisper server | `not-needed` | No |
| `DATABASE_URL` | PostgreSQL connection URL | (uses SQLite if not set) | No |
| `SQLITE_DB` | SQLite database path | `/opt/app-root/src/data/echonote.db` | No |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:5173` | Yes |
| `MAX_UPLOAD_SIZE` | Max file upload size in bytes | `104857600` (100MB) | No |

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

Edit `echonote-kube.yaml` and add `DATABASE_URL` to the ConfigMap:

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
podman kube down echonote-kube.yaml
podman kube play echonote-kube.yaml
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
# View logs (podman kube play)
podman logs -f echonote-backend-backend

# View pod logs
podman pod logs echonote-backend

# For podman run deployments
podman logs -f echonote-backend
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

After editing `echonote-kube.yaml`, you must restart:
```bash
podman kube down echonote-kube.yaml
podman kube play echonote-kube.yaml
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
podman exec -it echonote-backend-backend /bin/sh

# Test connection (if curl is available)
curl http://your-whisper-server:8080/v1/models
```

If running locally, use host.containers.internal:
```yaml
MODEL_URL: "http://host.containers.internal:8080/v1"
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
podman kube generate echonote-backend > my-echonote-kube.yaml
```

## Systemd Integration (Auto-start on Boot)

Podman can generate systemd unit files for automatic startup:

```bash
# Deploy with podman kube play first
podman kube play echonote-kube.yaml

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
# Build for AMD64
podman build --platform linux/amd64 -t localhost/echonote-backend:amd64 -f Containerfile .

# Build for ARM64
podman build --platform linux/arm64 -t localhost/echonote-backend:arm64 -f Containerfile .

# Create manifest for multi-arch
podman manifest create localhost/echonote-backend:latest
podman manifest add localhost/echonote-backend:latest localhost/echonote-backend:amd64
podman manifest add localhost/echonote-backend:latest localhost/echonote-backend:arm64
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
