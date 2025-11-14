"""
Audio format conversion utilities.

This module provides WebM to WAV audio conversion using subprocess isolation
to prevent ffmpeg/pydub from interfering with the diarization pipeline's
memory usage.

Technical Notes:
    - Uses pydub + ffmpeg for audio format conversion
    - Runs conversion in isolated subprocess that terminates before returning
    - Prevents memory conflicts with PyTorch/pyannote.audio
    - Requires ffmpeg system package
    - Supports 30-second timeout for conversion operations
"""

import logging
import subprocess
import sys
from io import BytesIO

logger = logging.getLogger(__name__)




def convert_audio_to_wav(audio_bytes: bytes, source_format: str = "webm") -> tuple[bytes, float | None]:
    """
    Convert audio to WAV format in isolated subprocess.

    This function runs pydub/ffmpeg in a completely separate process
    that terminates before returning, ensuring no memory conflicts
    with the diarization pipeline.

    Args:
        audio_bytes: Audio data as bytes
        source_format: Source audio format (webm, mp3, etc.)

    Returns:
        Tuple of (WAV audio data as bytes, duration in seconds or None)

    Raises:
        Exception: If conversion fails or times out (30s timeout)

    Example:
        >>> with open("audio.mp3", "rb") as f:
        ...     audio_data = f.read()
        >>> wav_data, duration = convert_audio_to_wav(audio_data, "mp3")
        >>> print(f"Duration: {duration} seconds")
        >>> with open("audio.wav", "wb") as f:
        ...     f.write(wav_data)
    """
    logger.info(f"Converting {source_format.upper()} to WAV in isolated subprocess")

    # Create Python script to run in subprocess
    # This script reads audio from stdin and writes WAV to stdout
    script = f'''
import sys
from io import BytesIO
from pydub import AudioSegment

# Read audio from stdin
audio_bytes = sys.stdin.buffer.read()

# Convert to AudioSegment (uses ffmpeg internally)
audio = AudioSegment.from_file(BytesIO(audio_bytes), format="{source_format}")

# Log conversion details to stderr (doesn't interfere with stdout data)
print(f"LOADED: duration={{len(audio)}}ms, channels={{audio.channels}}, rate={{audio.frame_rate}}Hz", file=sys.stderr)

# Export as WAV format
wav_buffer = BytesIO()
audio.export(wav_buffer, format="wav")

# Write WAV data to stdout
sys.stdout.buffer.write(wav_buffer.getvalue())
'''

    try:
        # Run conversion in isolated subprocess
        # The subprocess exits after conversion, ensuring no memory leaks
        result = subprocess.run(
            [sys.executable, '-c', script],
            input=audio_bytes,
            capture_output=True,
            check=True,
            timeout=30  # 30-second timeout for safety
        )

        # Log conversion details from subprocess stderr and extract duration
        duration_seconds = None
        if result.stderr:
            stderr_output = result.stderr.decode().strip()
            logger.info(f"Subprocess output: {stderr_output}")

            # Extract duration from output: "LOADED: duration=3494ms, ..."
            try:
                import re
                duration_match = re.search(r'duration=(\d+)ms', stderr_output)
                if duration_match:
                    duration_ms = int(duration_match.group(1))
                    duration_seconds = duration_ms / 1000.0
            except Exception as e:
                logger.warning(f"Could not parse duration from subprocess output: {e}")

        # Get WAV data from subprocess stdout
        wav_bytes = result.stdout
        logger.info(
            f"Converted to WAV: {len(wav_bytes)} bytes "
            f"(subprocess completed and terminated)"
        )

        return wav_bytes, duration_seconds

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        logger.error(f"Subprocess conversion failed: {error_msg}")
        raise Exception(f"{source_format.upper()} to WAV conversion failed: {error_msg}")
    except subprocess.TimeoutExpired:
        logger.error("Subprocess conversion timed out after 30 seconds")
        raise Exception(f"{source_format.upper()} to WAV conversion timed out")


def convert_webm_to_wav(webm_bytes: bytes) -> tuple[bytes, float | None]:
    """
    Convert WebM audio to WAV format in isolated subprocess.

    This is a convenience wrapper around convert_audio_to_wav() for backward compatibility.

    Args:
        webm_bytes: WebM audio data as bytes

    Returns:
        Tuple of (WAV audio data as bytes, duration in seconds or None)

    Raises:
        Exception: If conversion fails or times out (30s timeout)

    Example:
        >>> with open("audio.webm", "rb") as f:
        ...     webm_data = f.read()
        >>> wav_data, duration = convert_webm_to_wav(webm_data)
        >>> print(f"Duration: {duration} seconds")
        >>> with open("audio.wav", "wb") as f:
        ...     f.write(wav_data)
    """
    return convert_audio_to_wav(webm_bytes, source_format="webm")
