# Speaker Diarization Guide

EchoNote supports optional speaker diarization using pyannote.audio, which can detect and separate different speakers in your audio recordings.

## Overview

Speaker diarization answers the question "who spoke when?" by:
- Detecting voice activity in the audio
- Identifying different speakers
- Providing timestamps for each speaker's segments
- Transcribing each speaker segment individually for accurate speaker labeling

## Setup

### 1. Install Dependencies

The CPU-only PyTorch packages are included in `backend/requirements.txt`:

```bash
pip install -r backend/requirements.txt
```

This installs:
- `torch==2.8.0+cpu` (CPU-only, ~150MB instead of ~2GB with CUDA)
- `torchaudio==2.8.0+cpu`
- `pyannote.audio==3.3.2` (pinned version for stability)
- `matplotlib>=3.6,<3.10` (required by pyannote, pinned to avoid crashes)
- `soundfile` (for audio I/O)
- `pydub` (for WebM to WAV conversion)

**Important**: The exact version pins in `requirements.txt` are critical for stability. See "Version Compatibility" section below for details.

### 2. Get Hugging Face Token

1. Create an account at [Hugging Face](https://huggingface.co)
2. Go to [Settings → Tokens](https://huggingface.co/settings/tokens)
3. Create a new token (read access is sufficient)
4. Accept the model license at [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)

### 3. Configure Environment

Add to your `.env` file:

```bash
HF_TOKEN=hf_your_actual_token_here
DIARIZATION_MODEL=pyannote/speaker-diarization-3.1  # Optional, this is the default
```

## Usage

### From the UI

1. Before recording, check the **"Enable speaker diarization"** checkbox
2. (Optional) Enter the number of speakers if you know it
   - Leave empty for automatic detection
   - Specifying the number can improve accuracy
3. Record and transcribe as usual

### Example Output

With diarization enabled, the transcription includes speaker labels and timestamps:

```
[SPEAKER_00] Hello, welcome to our meeting today. (0.5s - 3.2s)
[SPEAKER_01] Thanks for having me. Let's discuss the project. (3.5s - 7.1s)
[SPEAKER_00] Great. I'd like to start with the timeline. (7.4s - 10.2s)
[SPEAKER_01] Sounds good. I think we can complete it in two weeks. (10.5s - 14.3s)
```

**How it works:**
1. The audio is first analyzed to identify speaker segments (diarization)
2. Each speaker segment is then individually transcribed
3. The transcriptions are combined with speaker labels and timestamps

### From the API

```bash
curl -X POST "http://localhost:8000/api/transcribe" \
  -F "file=@recording.wav" \
  -F "enable_diarization=true" \
  -F "num_speakers=2"
```

## Technical Details

### Model

- **Model**: pyannote/speaker-diarization-3.1
- **Library Version**: pyannote.audio 3.3.2
- **Size**: ~300MB (downloads on first use)
- **Performance**: CPU-only, runs efficiently on most hardware
- **Accuracy**: State-of-the-art speaker diarization

### Architecture

The complete pipeline consists of:

1. **Audio Conversion** (if needed):
   - WebM files are converted to WAV in an isolated subprocess
   - Prevents memory conflicts between pydub/ffmpeg and PyTorch

2. **Speaker Diarization**:
   - **Voice Activity Detection (VAD)** - Detects when speech occurs
   - **Speaker Embedding** - Extracts speaker characteristics
   - **Clustering** - Groups segments by speaker identity
   - Lazy-loaded on first use to save memory

3. **Segment Transcription**:
   - Audio is split by speaker segments
   - Each segment is transcribed individually using Whisper
   - Results are combined with speaker labels and timestamps

### Performance Considerations

- **First Use**: Model downloads (~300MB), takes a few minutes
- **Subsequent Uses**: Model is cached, much faster
- **Processing Time**: Depends on number of speakers and audio length
  - Diarization: ~2-5x audio duration
  - Transcription: ~N speaker segments × transcription time per segment
  - Example: 30 second audio with 4 speakers = 1-3 minutes total
- **Memory**: ~4-8GB RAM recommended for stable operation

## Version Compatibility

### Why pyannote.audio 3.3.2?

EchoNote uses `pyannote.audio==3.3.2` instead of the latest 4.x version due to a critical compatibility issue:

**The Problem:**
- pyannote.audio 4.0.1+ requires `matplotlib>=3.10.0`
- matplotlib 3.10.x has a font_manager bug that causes `std::bad_alloc` crashes
- This crash occurs even with 28GB RAM, making the system completely unusable
- The crash happens during font manager initialization, before any actual processing

**The Solution:**
- Use pyannote.audio 3.3.2 which works with `matplotlib<3.10`
- matplotlib 3.9.x is stable and doesn't have the font_manager crash
- This combination provides reliable operation with normal memory usage (4-8GB)

**API Differences (pyannote 3.x vs 4.x):**

When upgrading pyannote.audio in the future, be aware of these API changes:

```python
# Version 3.x (current)
pipeline = Pipeline.from_pretrained(
    model_name,
    use_auth_token=token  # 3.x parameter name
)
diarization = pipeline(audio)
for turn, _, speaker in diarization.itertracks(yield_label=True):
    # Process segments

# Version 4.x (future)
pipeline = Pipeline.from_pretrained(
    model_name,
    token=token  # 4.x parameter name (changed!)
)
diarization = pipeline(audio)
# Result parsing may differ - check 4.x docs
```

**Future Upgrade Path:**

Before upgrading to pyannote.audio 4.x:

1. **Verify matplotlib compatibility**: Check if matplotlib 3.10+ font_manager bug is fixed
2. **Test thoroughly**: Run diarization with various audio files and monitor for crashes
3. **Update API calls**: Change `use_auth_token` → `token` parameter
4. **Update huggingface_hub**: Remove version pin (4.x uses newer API)
5. **Check result parsing**: Verify `diarization.itertracks()` still works the same way
6. **Monitor memory**: Test with production-sized audio files

**System Requirements:**
- `libsndfile` (for soundfile audio I/O)
- `ffmpeg` (for WebM conversion via pydub)

## Limitations

1. **Speaker Labels**: Speakers are labeled as SPEAKER_00, SPEAKER_01, etc.
   - The model doesn't know who the speakers are
   - It only separates them by voice characteristics

2. **Language**: Works with any language (voice-based, not text-based)

3. **Audio Quality**: Performance degrades with:
   - Background noise
   - Overlapping speech
   - Poor recording quality

4. **Number of Speakers**:
   - Auto-detection works well for 2-10 speakers (min_speakers=2, max_speakers=10)
   - Specifying the exact number improves accuracy
   - More than 10 speakers may require manual configuration

5. **Short Segments**: Segments shorter than 0.5 seconds are skipped to avoid transcription errors

## Troubleshooting

### Error: "HF_TOKEN not set"

**Solution**: Add your Hugging Face token to `.env`:
```bash
HF_TOKEN=hf_your_token_here
```

### Error: "Cannot access gated model"

**Solution**: Accept the model license at https://huggingface.co/pyannote/speaker-diarization-3.1

### Error: "std::bad_alloc" crash

**Symptom**: Application crashes with `terminate called after throwing an instance of 'std::bad_alloc'` after "matplotlib.font_manager" log message

**Solution**: This indicates pyannote.audio 4.x was installed instead of 3.3.2. Fix with:
```bash
pip uninstall pyannote.audio matplotlib -y
pip install -r backend/requirements.txt
```

Verify correct versions:
```bash
pip show pyannote.audio matplotlib
# Should show: pyannote.audio 3.3.2 and matplotlib 3.9.x
```

### Error: "CUDA packages installed"

**Solution**: Ensure you're installing from `requirements.txt` which includes the `--extra-index-url` directive:
```bash
pip install -r backend/requirements.txt
```

### Slow Performance

**Tips**:
- First run is always slower (model download)
- Diarization is CPU-intensive, consider:
  - Using shorter audio clips
  - Increasing CPU resources
  - Disabling diarization for quick transcriptions

### Poor Diarization Results

**Tips**:
- Ensure good audio quality
- Minimize background noise
- Specify the number of speakers if known
- Check that speakers have distinct voices
- Avoid overlapping speech

## Cost Considerations

- **Model**: Free and open source
- **Compute**: Runs on CPU, no GPU needed
- **Storage**: ~300MB for model cache
- **Network**: One-time download of ~300MB

## Disabling Diarization

Diarization is **disabled by default**. Users must opt-in via:
- UI checkbox
- API parameter `enable_diarization=true`

To completely remove diarization support:
1. Remove from `backend/requirements.txt`:
   - torch
   - torchaudio
   - pyannote.audio
2. Remove `backend/diarization.py`
3. Remove diarization code from `backend/main.py`

## References

- [pyannote.audio Documentation](https://github.com/pyannote/pyannote-audio)
- [pyannote.audio 3.3.2 Release](https://github.com/pyannote/pyannote-audio/releases/tag/3.3.2)
- [Speaker Diarization 3.1 Model](https://huggingface.co/pyannote/speaker-diarization-3.1)
- [Hugging Face Tokens](https://huggingface.co/docs/hub/security-tokens)
- [matplotlib 3.10 font_manager issue](https://github.com/matplotlib/matplotlib/issues/28567)
