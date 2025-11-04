# Model Configuration Guide

This guide explains how to configure multiple transcription models in EchoNote.

## Overview

EchoNote supports multiple Whisper transcription models. Users can select which model to use before recording a voice message. Each model can have its own base URL, allowing you to use different model endpoints or versions.

---

## Configuration Methods

### Method 1: Multiple Models (JSON Format)

Configure multiple models using the `MODELS` environment variable with JSON format:

**Environment Variables:**
```bash
# JSON object mapping model names to base URLs
export MODELS='{"whisper-large-v3": "https://model1.example.com/v1", "whisper-medium": "https://model2.example.com/v1", "whisper-small": "https://model3.example.com/v1"}'

# Specify which model is the default (optional)
export DEFAULT_MODEL="whisper-large-v3"

# API key for authentication (if required)
export API_KEY="your-api-key-here"
```

**Notes:**
- The `MODELS` value must be valid JSON
- Model names are displayed in the frontend dropdown (use descriptive names)
- If `DEFAULT_MODEL` is not set or invalid, the first model in the list will be used as default
- All models should use OpenAI-compatible Whisper API endpoints

---

### Method 2: Single Model (Legacy)

For backward compatibility, you can still configure a single model using the legacy format:

**Environment Variables:**
```bash
export MODEL_NAME="whisper-large-v3-turbo-quantizedw4a16"
export MODEL_URL="https://whisper-large-v3-turbo-quantizedw4a16-models.apps.ai3.pgustafs.com/v1"
export API_KEY="EMPTY"
```

**Notes:**
- This is the current default configuration
- If `MODELS` is not set, the system falls back to `MODEL_NAME` and `MODEL_URL`
- The model selector will show only one option

---

## Example Configurations

### Example 1: Three Different Model Sizes

```bash
# Configure three models with different sizes
export MODELS='{
  "whisper-large-v3": "https://whisper-large.example.com/v1",
  "whisper-medium": "https://whisper-medium.example.com/v1",
  "whisper-small": "https://whisper-small.example.com/v1"
}'

export DEFAULT_MODEL="whisper-medium"
export API_KEY="your-api-key"
```

**Result:** Users can choose between Large (most accurate), Medium (balanced), or Small (fastest) models.

---

### Example 2: Different Languages

```bash
# Configure models optimized for different languages
export MODELS='{
  "whisper-large-v3-english": "https://whisper-english.example.com/v1",
  "whisper-large-v3-multilingual": "https://whisper-multi.example.com/v1"
}'

export DEFAULT_MODEL="whisper-large-v3-english"
export API_KEY="your-api-key"
```

**Result:** Users can choose between English-only or multilingual models.

---

### Example 3: Quantized vs Full Precision

```bash
# Configure models with different precision levels
export MODELS='{
  "whisper-large-v3-turbo-quantized": "https://whisper-quantized.example.com/v1",
  "whisper-large-v3-turbo-full": "https://whisper-full.example.com/v1"
}'

export DEFAULT_MODEL="whisper-large-v3-turbo-quantized"
export API_KEY="EMPTY"
```

**Result:** Users can choose between quantized (faster, lower resource) or full precision (higher quality) models.

---

## Setting Environment Variables

### Option 1: Direct Export (Development)

```bash
export MODELS='{"model1": "https://...", "model2": "https://..."}'
export DEFAULT_MODEL="model1"
export API_KEY="your-key"

# Run the backend
cd backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

---

### Option 2: .env File (Development)

Create a `.env` file in the project root:

```bash
# .env
MODELS={"whisper-large": "https://model1.example.com/v1", "whisper-medium": "https://model2.example.com/v1"}
DEFAULT_MODEL=whisper-large
API_KEY=your-api-key-here
```

Then load it before running:

```bash
# Load environment variables
source .env

# Or use a tool like direnv or dotenv
```

**Note:** The `.env` file is gitignored by default to protect sensitive information.

---

### Option 3: Podman/Docker Environment Variables

#### Using podman run

```bash
podman run -d \
  --name echonote-backend \
  -p 8000:8000 \
  -e MODELS='{"whisper-large": "https://model1.example.com/v1", "whisper-medium": "https://model2.example.com/v1"}' \
  -e DEFAULT_MODEL="whisper-large" \
  -e API_KEY="your-api-key" \
  localhost/echonote-backend:latest
```

#### Using Kubernetes YAML

Update your `echonote-kube.yaml` file:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: echonote
spec:
  containers:
  - name: backend
    image: localhost/echonote-backend:latest
    env:
    - name: MODELS
      value: '{"whisper-large": "https://model1.example.com/v1", "whisper-medium": "https://model2.example.com/v1"}'
    - name: DEFAULT_MODEL
      value: "whisper-large"
    - name: API_KEY
      value: "your-api-key"
```

Then deploy:

```bash
podman kube play echonote-kube.yaml
```

---

### Option 4: Kubernetes ConfigMap/Secret

For production deployments, use ConfigMaps and Secrets:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: echonote-config
data:
  models: |
    {
      "whisper-large-v3": "https://whisper-large.example.com/v1",
      "whisper-medium": "https://whisper-medium.example.com/v1"
    }
  default-model: "whisper-large-v3"
---
apiVersion: v1
kind: Secret
metadata:
  name: echonote-secrets
type: Opaque
stringData:
  api-key: "your-api-key-here"
---
apiVersion: v1
kind: Pod
metadata:
  name: echonote
spec:
  containers:
  - name: backend
    image: localhost/echonote-backend:latest
    env:
    - name: MODELS
      valueFrom:
        configMapKeyRef:
          name: echonote-config
          key: models
    - name: DEFAULT_MODEL
      valueFrom:
        configMapKeyRef:
          name: echonote-config
          key: default-model
    - name: API_KEY
      valueFrom:
        secretKeyRef:
          name: echonote-secrets
          key: api-key
```

---

## User Interface

Once configured, users will see the model selector in the recording interface:

1. **Before Recording:** A dropdown appears above the "Add URL to voice note" checkbox
2. **Model Selection:** Users can select from available models
3. **Default Selection:** The default model is pre-selected
4. **Recording:** After selecting a model, users click "Start Recording"
5. **Transcription:** The selected model is used for transcription

---

## API Endpoints

### GET /api/models

Returns available models and the default model.

**Request:**
```bash
curl http://localhost:8000/api/models
```

**Response:**
```json
{
  "models": [
    "whisper-large-v3",
    "whisper-medium",
    "whisper-small"
  ],
  "default": "whisper-large-v3"
}
```

---

### POST /api/transcribe

Transcribe audio with an optional model parameter.

**Request:**
```bash
curl -X POST http://localhost:8000/api/transcribe \
  -F "file=@recording.wav" \
  -F "model=whisper-medium"
```

**Response:**
```json
{
  "id": 1,
  "text": "This is the transcribed text",
  "audio_filename": "recording.wav",
  "created_at": "2025-11-03T20:00:00",
  "priority": "medium",
  "url": null
}
```

**Notes:**
- If `model` parameter is omitted, the default model is used
- If an invalid model is specified, a 400 error is returned

---

## Troubleshooting

### Models not appearing in dropdown

**Problem:** The frontend shows no model selector or empty dropdown.

**Solutions:**
1. Check backend logs: `podman logs echonote-backend | grep model`
2. Verify environment variables are set correctly
3. Test the API endpoint: `curl http://localhost:8000/api/models`
4. Ensure `MODELS` is valid JSON

---

### "Invalid model" error when transcribing

**Problem:** Transcription fails with "Invalid model" error.

**Solutions:**
1. Check the model name matches exactly (case-sensitive)
2. Verify the model exists in the `MODELS` configuration
3. Check backend logs for available models
4. Ensure the frontend is using the latest build

---

### Model URL not working

**Problem:** Transcription fails with connection errors.

**Solutions:**
1. Verify the base URL is correct and accessible
2. Check network connectivity from the backend container
3. Ensure the API key is correct (if required)
4. Test the endpoint directly:
   ```bash
   curl -H "Authorization: Bearer YOUR_KEY" https://model-url.example.com/v1/models
   ```

---

### JSON parsing error

**Problem:** Backend logs show "Failed to parse MODELS env var".

**Solutions:**
1. Validate your JSON: Use a tool like [JSONLint](https://jsonlint.com/)
2. Ensure proper escaping in shell:
   ```bash
   # Correct
   export MODELS='{"model1": "url1"}'

   # Incorrect (missing quotes)
   export MODELS={model1: url1}
   ```
3. For YAML files, ensure proper quoting:
   ```yaml
   # Correct
   - name: MODELS
     value: '{"model1": "url1"}'
   ```

---

## Best Practices

### 1. Use Descriptive Model Names
```bash
# Good - Clear purpose
"whisper-large-v3-english-fast"
"whisper-medium-multilingual-accurate"

# Bad - Unclear
"model1"
"m2"
```

### 2. Document Model Capabilities
Keep a reference of what each model does:
```bash
# whisper-large-v3: Best accuracy, slower, English-only
# whisper-medium: Balanced, multilingual
# whisper-small: Fastest, lower accuracy, good for real-time
```

### 3. Test Each Model
Before deploying, test each model endpoint:
```bash
# Test each model
for model in whisper-large whisper-medium whisper-small; do
  echo "Testing $model..."
  curl -X POST http://localhost:8000/api/transcribe \
    -F "file=@test.wav" \
    -F "model=$model"
done
```

### 4. Monitor Performance
Track which models users prefer and their performance:
- Transcription accuracy
- Processing time
- Resource usage
- User feedback

### 5. Security
- Never commit API keys to version control
- Use Kubernetes Secrets for sensitive data
- Rotate API keys regularly
- Limit network access to model endpoints

---

## Migration from Single to Multiple Models

If you're currently using the legacy single-model configuration:

**Current Configuration:**
```bash
export MODEL_NAME="whisper-large-v3"
export MODEL_URL="https://model.example.com/v1"
```

**Migrated Configuration:**
```bash
# Keep backward compatibility while adding more models
export MODELS='{
  "whisper-large-v3": "https://model.example.com/v1",
  "whisper-medium": "https://model2.example.com/v1"
}'
export DEFAULT_MODEL="whisper-large-v3"

# Remove old env vars (optional)
# unset MODEL_NAME
# unset MODEL_URL
```

**Result:** Existing behavior is preserved, but users can now choose additional models.

---

## Testing Your Configuration

### 1. Verify Backend Startup

```bash
podman logs echonote-backend 2>&1 | grep -i model
```

**Expected Output:**
```
Available models: ['whisper-large-v3', 'whisper-medium', 'whisper-small']
Default model: whisper-large-v3
```

---

### 2. Test Models API

```bash
curl http://localhost:8000/api/models | python3 -m json.tool
```

**Expected Output:**
```json
{
    "models": [
        "whisper-large-v3",
        "whisper-medium",
        "whisper-small"
    ],
    "default": "whisper-large-v3"
}
```

---

### 3. Test Transcription with Specific Model

```bash
# Create a test audio file (or use existing)
curl -X POST http://localhost:8000/api/transcribe \
  -F "file=@test.wav" \
  -F "model=whisper-medium"
```

**Expected:** Successful transcription using the specified model.

---

## Frontend Behavior

The frontend automatically:
1. Fetches available models on page load via `GET /api/models`
2. Displays a dropdown selector if multiple models are available
3. Pre-selects the default model
4. Sends the selected model with each transcription request
5. Falls back to the default model if none is selected

**UI Location:**
- The model selector appears in the recording card
- Located above the "Add URL to voice note" checkbox
- Only visible when not recording or transcribing

---

## Advanced Configuration

### Different API Keys per Model

If your models use different API keys, you'll need to modify the backend code:

**backend/config.py:**
```python
# Add a mapping of models to API keys
MODEL_API_KEYS: Dict[str, str] = {
    "whisper-large": os.getenv("WHISPER_LARGE_API_KEY", "key1"),
    "whisper-medium": os.getenv("WHISPER_MEDIUM_API_KEY", "key2"),
}

def get_api_key(self, model_name: str) -> str:
    return self.MODEL_API_KEYS.get(model_name, self.API_KEY)
```

**backend/main.py:**
```python
# In transcribe_audio function
api_key = settings.get_api_key(selected_model)
client = AsyncOpenAI(
    base_url=model_base_url,
    api_key=api_key,
)
```

---

## Support

For additional help:
- Check backend logs: `podman logs echonote-backend`
- Check frontend logs: `podman logs echonote-frontend`
- Review the API documentation at `http://localhost:8000/docs`
- See the main README for general troubleshooting

---

**Last Updated:** 2025-11-03
**Version:** 1.0.0
