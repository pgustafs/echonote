"""
Speaker diarization service using pyannote.audio.

This module provides functionality to detect and separate different speakers
in audio files using the pyannote speaker diarization pipeline.

Technical Notes:
    - Uses pyannote.audio 3.3.2 for compatibility with matplotlib <3.10
    - Requires Hugging Face token for model access
    - Processes audio on CPU to avoid GPU dependencies
    - Uses soundfile for audio I/O (requires libsndfile system package)
"""

import logging
import os
import tempfile
from typing import Optional

import soundfile as sf
import torch
from pyannote.audio import Pipeline
from pyannote.audio.core.task import Specifications, Problem, Resolution
from pyannote.audio.core.model import Introspection
from omegaconf import DictConfig, ListConfig
from omegaconf.base import ContainerMetadata, Metadata
from omegaconf.nodes import AnyNode

from backend.config import settings

# Fix for PyTorch 2.6+: Add safe globals for model loading
# PyTorch 2.6+ changed weights_only default from False to True, which breaks
# loading of pyannote models that contain OmegaConf and pyannote classes
if hasattr(torch, 'serialization') and hasattr(torch.serialization, 'add_safe_globals'):
    torch.serialization.add_safe_globals([
        # PyTorch internal classes
        torch.torch_version.TorchVersion,
        # pyannote.audio core classes
        Specifications,
        Problem,
        Resolution,
        Introspection,
        # OmegaConf classes (required for model configuration)
        ListConfig,
        DictConfig,
        ContainerMetadata,
        Metadata,
        AnyNode,
    ])

logger = logging.getLogger(__name__)


class DiarizationService:
    """
    Service for speaker diarization using pyannote.audio.

    This service uses a singleton pattern to load the diarization model once
    and reuse it across multiple requests, improving performance.

    Attributes:
        _pipeline: Lazy-loaded pyannote Pipeline instance
    """

    def __init__(self):
        """Initialize the diarization service with no pre-loaded pipeline."""
        self._pipeline: Optional[Pipeline] = None

    def _load_pipeline(self) -> Pipeline:
        """
        Lazy load the diarization pipeline on first use.

        This method loads the pyannote.audio pipeline from Hugging Face Hub
        and configures it for CPU inference. The pipeline is cached for
        subsequent calls.

        Returns:
            Pipeline: Loaded and configured pyannote diarization pipeline

        Raises:
            Exception: If model loading fails (network issues, invalid token, etc.)
        """
        if self._pipeline is None:
            # Configure matplotlib to use minimal memory (required by pyannote)
            os.environ['MPLBACKEND'] = 'Agg'
            os.environ['MPLCONFIGDIR'] = '/tmp/matplotlib'

            logger.info(f"Loading diarization model: {settings.DIARIZATION_MODEL}")

            if not settings.HF_TOKEN:
                logger.warning(
                    "HF_TOKEN not set. Pyannote models require a Hugging Face token. "
                    "Get one at https://huggingface.co/settings/tokens and accept the model license."
                )

            try:
                # Load pipeline from Hugging Face Hub
                # Note: use_auth_token parameter is for pyannote.audio 3.x compatibility
                self._pipeline = Pipeline.from_pretrained(
                    settings.DIARIZATION_MODEL,
                    use_auth_token=settings.HF_TOKEN if settings.HF_TOKEN else None,
                )

                # Force CPU usage (no GPU required for this application)
                if torch.cuda.is_available():
                    logger.info("GPU available but forcing CPU usage for diarization")
                self._pipeline.to(torch.device("cpu"))

                logger.info("Diarization pipeline loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load diarization pipeline: {e}")
                raise

        return self._pipeline

    def diarize_audio(
        self,
        audio_bytes: bytes,
        num_speakers: Optional[int] = None,
    ) -> list:
        """
        Perform speaker diarization on audio data.

        This method identifies different speakers in the audio and returns
        timestamped segments for each speaker.

        Args:
            audio_bytes: Audio data as bytes (must be WAV format)
            num_speakers: Optional number of speakers if known. If None,
                         the algorithm will auto-detect (min=2, max=10)

        Returns:
            List of dicts with keys:
                - speaker (str): Speaker label (e.g., "SPEAKER_00")
                - start (float): Segment start time in seconds
                - end (float): Segment end time in seconds

        Raises:
            Exception: If audio processing or diarization fails

        Example:
            >>> service = get_diarization_service()
            >>> results = service.diarize_audio(wav_bytes, num_speakers=2)
            >>> for segment in results:
            ...     print(f"{segment['speaker']}: {segment['start']:.2f}s - {segment['end']:.2f}s")
        """
        pipeline = self._load_pipeline()

        # Write audio to temporary file for soundfile to read
        # (soundfile doesn't support reading from BytesIO for all formats)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name

        try:
            logger.info(f"Running diarization (num_speakers={num_speakers})")

            # Load audio with soundfile
            # pyannote.audio accepts pre-loaded audio as {'waveform': tensor, 'sample_rate': int}
            waveform, sample_rate = sf.read(tmp_path)
            logger.info(
                f"Loaded audio: shape={waveform.shape}, "
                f"sample_rate={sample_rate}, "
                f"duration={len(waveform)/sample_rate:.2f}s"
            )

            # Convert to torch tensor with correct shape (channels, samples)
            waveform_tensor = torch.from_numpy(waveform).float()
            if len(waveform_tensor.shape) == 1:
                # Mono audio: add channel dimension [samples] -> [1, samples]
                waveform_tensor = waveform_tensor.unsqueeze(0)
            else:
                # Stereo/multi-channel: transpose [samples, channels] -> [channels, samples]
                waveform_tensor = waveform_tensor.transpose(0, 1)

            logger.info(f"Prepared tensor: shape={waveform_tensor.shape}, dtype={waveform_tensor.dtype}")

            # Configure diarization parameters
            kwargs = {}
            if num_speakers is not None:
                kwargs["num_speakers"] = num_speakers
            else:
                # Auto-detect mode: assume conversation (min 2 speakers)
                kwargs["min_speakers"] = 2
                kwargs["max_speakers"] = 10
                logger.info("Auto-detect mode: setting min_speakers=2, max_speakers=10")

            # Run diarization using file path (pyannote pipeline prefers file paths)
            diarization = pipeline(tmp_path, **kwargs)

            # Parse results from pyannote.audio 3.x Annotation object
            results = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                results.append({
                    "speaker": speaker,
                    "start": turn.start,
                    "end": turn.end,
                })

            unique_speakers = len(set(r['speaker'] for r in results))
            logger.info(f"Diarization complete: found {unique_speakers} speakers in {len(results)} segments")

            return results

        finally:
            # Clean up temporary file
            try:
                os.unlink(tmp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")

    def format_diarization_results(self, results: list) -> str:
        """
        Format diarization results as human-readable text.

        Args:
            results: List of diarization segments from diarize_audio()

        Returns:
            Formatted string with speaker timeline, or empty string if no results

        Example:
            === Speaker Timeline ===
            SPEAKER_00: 0.50s - 3.20s (duration: 2.70s)
            SPEAKER_01: 3.50s - 5.80s (duration: 2.30s)
        """
        if not results:
            return ""

        lines = ["=== Speaker Timeline ==="]
        for segment in results:
            speaker = segment["speaker"]
            start = segment["start"]
            end = segment["end"]
            duration = end - start
            lines.append(
                f"{speaker}: {start:.2f}s - {end:.2f}s (duration: {duration:.2f}s)"
            )

        return "\n".join(lines)


# Global singleton instance
_diarization_service: Optional[DiarizationService] = None


def get_diarization_service() -> DiarizationService:
    """
    Get or create the global diarization service singleton.

    This function implements the singleton pattern to ensure only one
    diarization pipeline is loaded in memory, improving performance
    and resource usage.

    Returns:
        DiarizationService: Singleton diarization service instance

    Example:
        >>> service = get_diarization_service()
        >>> results = service.diarize_audio(audio_bytes)
    """
    global _diarization_service
    if _diarization_service is None:
        _diarization_service = DiarizationService()
    return _diarization_service
