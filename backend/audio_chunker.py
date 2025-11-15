"""
Audio chunking utility for splitting long recordings into manageable segments.

This module provides functionality to chunk audio files for processing long
recordings that exceed model input limits. Supports two modes:

1. Time-based chunking: Split audio into fixed-duration chunks (e.g., 60 seconds)
2. Diarization-aware chunking: Split based on speaker segments, with sub-chunking
   if a speaker's segment exceeds the chunk duration limit

Architecture:
    - Uses pydub for audio manipulation
    - Returns chunks as WAV bytes for consistent format
    - Tracks timestamps for each chunk for proper merging
    - Handles edge cases (short audio, partial final chunks)

Usage:
    # Time-based chunking
    chunks = chunk_audio(audio_bytes, chunk_duration_seconds=60)
    for chunk_bytes, start_time, end_time in chunks:
        # Process each chunk
        pass

    # Diarization-aware chunking
    diarization_results = [
        {'speaker': 'SPEAKER_00', 'start': 0.0, 'end': 45.0},
        {'speaker': 'SPEAKER_01', 'start': 45.0, 'end': 90.0},
    ]
    chunks = chunk_audio_by_diarization(
        audio_bytes,
        diarization_results,
        max_chunk_duration=60
    )
"""

import logging
from io import BytesIO
from typing import List, Tuple, Dict
from pydub import AudioSegment

logger = logging.getLogger(__name__)


def chunk_audio(
    audio_bytes: bytes,
    chunk_duration_seconds: int = 60,
    source_format: str = "wav"
) -> List[Tuple[bytes, float, float]]:
    """
    Split audio into fixed-duration chunks.

    Args:
        audio_bytes: Audio data as bytes
        chunk_duration_seconds: Duration of each chunk in seconds (default: 60)
        source_format: Format of input audio (wav, webm, mp3, etc.)

    Returns:
        List of tuples: (chunk_bytes, start_time_seconds, end_time_seconds)

    Example:
        >>> chunks = chunk_audio(wav_data, chunk_duration_seconds=60)
        >>> print(f"Created {len(chunks)} chunks")
        >>> for chunk_bytes, start, end in chunks:
        ...     print(f"Chunk: {start:.2f}s - {end:.2f}s ({len(chunk_bytes)} bytes)")
    """
    logger.info(f"Starting audio chunking with {chunk_duration_seconds}s chunks")

    try:
        # Load audio
        audio = AudioSegment.from_file(BytesIO(audio_bytes), format=source_format)
        duration_seconds = len(audio) / 1000.0  # pydub works in milliseconds
        logger.info(f"Loaded audio: duration={duration_seconds:.2f}s, channels={audio.channels}, rate={audio.frame_rate}Hz")

        # Check if chunking is needed
        if duration_seconds <= chunk_duration_seconds:
            logger.info(f"Audio duration ({duration_seconds:.2f}s) <= chunk size ({chunk_duration_seconds}s), no chunking needed")
            # Return entire audio as single chunk
            wav_buffer = BytesIO()
            audio.export(wav_buffer, format="wav")
            return [(wav_buffer.getvalue(), 0.0, duration_seconds)]

        # Calculate chunk parameters
        chunk_duration_ms = chunk_duration_seconds * 1000
        total_duration_ms = len(audio)
        num_chunks = (total_duration_ms + chunk_duration_ms - 1) // chunk_duration_ms  # Ceiling division

        logger.info(f"Splitting audio into {num_chunks} chunks of {chunk_duration_seconds}s each")

        chunks = []
        for i in range(num_chunks):
            start_ms = i * chunk_duration_ms
            end_ms = min(start_ms + chunk_duration_ms, total_duration_ms)

            # Extract chunk
            chunk = audio[start_ms:end_ms]

            # Convert to WAV bytes
            wav_buffer = BytesIO()
            chunk.export(wav_buffer, format="wav")
            chunk_bytes = wav_buffer.getvalue()

            # Calculate timestamps in seconds
            start_seconds = start_ms / 1000.0
            end_seconds = end_ms / 1000.0

            chunks.append((chunk_bytes, start_seconds, end_seconds))
            logger.debug(f"Chunk {i+1}/{num_chunks}: {start_seconds:.2f}s - {end_seconds:.2f}s ({len(chunk_bytes)} bytes)")

        logger.info(f"Successfully created {len(chunks)} audio chunks")
        return chunks

    except Exception as e:
        logger.error(f"Failed to chunk audio: {e}", exc_info=True)
        raise


def chunk_audio_by_diarization(
    audio_bytes: bytes,
    diarization_results: List[Dict],
    max_chunk_duration: int = 60,
    source_format: str = "wav"
) -> List[Tuple[bytes, float, float, str]]:
    """
    Split audio based on speaker diarization results, with sub-chunking for long segments.

    This function chunks audio according to speaker segments from diarization.
    If a speaker's segment exceeds max_chunk_duration, it will be further split
    into smaller chunks.

    Args:
        audio_bytes: Audio data as bytes
        diarization_results: List of diarization segments with 'speaker', 'start', 'end'
        max_chunk_duration: Maximum duration for any chunk in seconds (default: 60)
        source_format: Format of input audio (wav, webm, mp3, etc.)

    Returns:
        List of tuples: (chunk_bytes, start_time_seconds, end_time_seconds, speaker_label)

    Example:
        >>> diarization = [
        ...     {'speaker': 'SPEAKER_00', 'start': 0.0, 'end': 45.0},
        ...     {'speaker': 'SPEAKER_01', 'start': 45.0, 'end': 150.0},  # Long segment, will be chunked
        ... ]
        >>> chunks = chunk_audio_by_diarization(wav_data, diarization, max_chunk_duration=60)
        >>> for chunk_bytes, start, end, speaker in chunks:
        ...     print(f"{speaker}: {start:.2f}s - {end:.2f}s")
    """
    logger.info(f"Starting diarization-aware chunking with max chunk duration={max_chunk_duration}s")
    logger.info(f"Processing {len(diarization_results)} diarization segments")

    try:
        # Load audio
        audio = AudioSegment.from_file(BytesIO(audio_bytes), format=source_format)
        logger.info(f"Loaded audio: duration={len(audio)/1000.0:.2f}s, channels={audio.channels}, rate={audio.frame_rate}Hz")

        chunks = []
        max_chunk_duration_ms = max_chunk_duration * 1000

        for seg_idx, segment in enumerate(diarization_results):
            speaker = segment['speaker']
            start_seconds = segment['start']
            end_seconds = segment['end']
            segment_duration = end_seconds - start_seconds

            logger.debug(f"Processing segment {seg_idx+1}/{len(diarization_results)}: {speaker} {start_seconds:.2f}s - {end_seconds:.2f}s (duration: {segment_duration:.2f}s)")

            # Check if segment needs sub-chunking
            if segment_duration <= max_chunk_duration:
                # Segment fits in one chunk
                start_ms = int(start_seconds * 1000)
                end_ms = int(end_seconds * 1000)

                # Extract segment
                chunk = audio[start_ms:end_ms]

                # Convert to WAV bytes
                wav_buffer = BytesIO()
                chunk.export(wav_buffer, format="wav")
                chunk_bytes = wav_buffer.getvalue()

                chunks.append((chunk_bytes, start_seconds, end_seconds, speaker))
                logger.debug(f"  Added chunk: {start_seconds:.2f}s - {end_seconds:.2f}s ({len(chunk_bytes)} bytes)")

            else:
                # Segment is too long, need to sub-chunk it
                num_sub_chunks = int((segment_duration + max_chunk_duration - 1) // max_chunk_duration)
                logger.info(f"  Segment {speaker} is {segment_duration:.2f}s long, splitting into {num_sub_chunks} sub-chunks")

                sub_chunk_duration = segment_duration / num_sub_chunks

                for sub_idx in range(num_sub_chunks):
                    sub_start_seconds = start_seconds + (sub_idx * sub_chunk_duration)
                    sub_end_seconds = min(start_seconds + ((sub_idx + 1) * sub_chunk_duration), end_seconds)

                    sub_start_ms = int(sub_start_seconds * 1000)
                    sub_end_ms = int(sub_end_seconds * 1000)

                    # Extract sub-chunk
                    sub_chunk = audio[sub_start_ms:sub_end_ms]

                    # Convert to WAV bytes
                    wav_buffer = BytesIO()
                    sub_chunk.export(wav_buffer, format="wav")
                    chunk_bytes = wav_buffer.getvalue()

                    chunks.append((chunk_bytes, sub_start_seconds, sub_end_seconds, speaker))
                    logger.debug(f"    Sub-chunk {sub_idx+1}/{num_sub_chunks}: {sub_start_seconds:.2f}s - {sub_end_seconds:.2f}s ({len(chunk_bytes)} bytes)")

        logger.info(f"Successfully created {len(chunks)} chunks from {len(diarization_results)} diarization segments")
        return chunks

    except Exception as e:
        logger.error(f"Failed to chunk audio by diarization: {e}", exc_info=True)
        raise
