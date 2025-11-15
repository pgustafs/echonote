"""
Transcription merger utility for combining chunked transcription results.

This module provides functionality to merge multiple transcription chunks
back into a single coherent transcript. Supports:

1. Simple concatenation for time-based chunks
2. Speaker-labeled formatting for diarization results
3. Optional timestamp markers

Usage:
    # Simple merge
    chunks = [
        {'text': 'Hello world', 'start': 0.0, 'end': 2.0},
        {'text': 'How are you?', 'start': 2.0, 'end': 4.0},
    ]
    result = merge_transcriptions(chunks)

    # Diarization merge with speaker labels
    chunks = [
        {'text': 'Hello', 'start': 0.0, 'end': 2.0, 'speaker': 'SPEAKER_00'},
        {'text': 'Hi there', 'start': 2.0, 'end': 4.0, 'speaker': 'SPEAKER_01'},
    ]
    result = merge_transcriptions(chunks, include_speakers=True)
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def merge_transcriptions(
    chunks: List[Dict],
    include_timestamps: bool = False,
    include_speakers: bool = False
) -> str:
    """
    Merge multiple transcription chunks into a single transcript.

    Args:
        chunks: List of chunk dictionaries with 'text', 'start', 'end' fields
                Optionally includes 'speaker' field for diarization results
        include_timestamps: Add timestamp markers in format [MM:SS - MM:SS]
        include_speakers: Add speaker labels (requires 'speaker' field in chunks)

    Returns:
        Merged transcription text

    Example:
        >>> chunks = [
        ...     {'text': 'Hello world', 'start': 0.0, 'end': 2.5},
        ...     {'text': 'How are you?', 'start': 2.5, 'end': 5.0},
        ... ]
        >>> print(merge_transcriptions(chunks))
        Hello world How are you?

        >>> print(merge_transcriptions(chunks, include_timestamps=True))
        [00:00 - 00:02] Hello world
        [00:02 - 00:05] How are you?

        >>> chunks_with_speakers = [
        ...     {'text': 'Hello', 'start': 0.0, 'end': 2.0, 'speaker': 'SPEAKER_00'},
        ...     {'text': 'Hi', 'start': 2.0, 'end': 3.0, 'speaker': 'SPEAKER_01'},
        ... ]
        >>> print(merge_transcriptions(chunks_with_speakers, include_speakers=True))
        SPEAKER_00: Hello
        SPEAKER_01: Hi
    """
    logger.info(f"Merging {len(chunks)} transcription chunks (timestamps={include_timestamps}, speakers={include_speakers})")

    if not chunks:
        logger.warning("No chunks to merge, returning empty string")
        return ""

    merged_lines = []

    for chunk in chunks:
        text = chunk.get('text', '').strip()
        if not text:
            logger.debug(f"Skipping empty chunk: {chunk.get('start', 0):.2f}s - {chunk.get('end', 0):.2f}s")
            continue

        line_parts = []

        # Add timestamp if requested
        if include_timestamps:
            start = chunk.get('start', 0)
            end = chunk.get('end', 0)
            timestamp = format_timestamp_range(start, end)
            line_parts.append(timestamp)

        # Add speaker if requested and available
        if include_speakers and 'speaker' in chunk:
            speaker = chunk['speaker']
            if include_timestamps:
                line_parts.append(f"{speaker}:")
            else:
                line_parts.append(f"{speaker}:")

        # Add transcription text
        line_parts.append(text)

        # Join parts and add to output
        if include_timestamps or include_speakers:
            merged_lines.append(' '.join(line_parts))
        else:
            merged_lines.append(text)

    # Join all lines
    if include_timestamps or include_speakers:
        result = '\n'.join(merged_lines)
    else:
        # Simple concatenation with space
        result = ' '.join(merged_lines)

    logger.info(f"Merge completed: {len(result)} characters, {len(merged_lines)} lines")
    return result


def format_timestamp_range(start_seconds: float, end_seconds: float) -> str:
    """
    Format timestamp range as [MM:SS - MM:SS].

    Args:
        start_seconds: Start time in seconds
        end_seconds: End time in seconds

    Returns:
        Formatted timestamp string

    Example:
        >>> format_timestamp_range(0, 65)
        '[00:00 - 01:05]'
        >>> format_timestamp_range(125.5, 190.2)
        '[02:05 - 03:10]'
    """
    def format_time(seconds):
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    return f"[{format_time(start_seconds)} - {format_time(end_seconds)}]"


def format_timestamp(seconds: float) -> str:
    """
    Format single timestamp as [MM:SS].

    Args:
        seconds: Time in seconds

    Returns:
        Formatted timestamp string

    Example:
        >>> format_timestamp(65)
        '[01:05]'
        >>> format_timestamp(125.5)
        '[02:05]'
    """
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"[{minutes:02d}:{secs:02d}]"


def group_by_speaker(chunks: List[Dict]) -> List[Dict]:
    """
    Group consecutive chunks by the same speaker.

    Combines consecutive chunks from the same speaker into single segments.
    Useful for diarization results where speaker may have multiple consecutive segments.

    Args:
        chunks: List of chunks with 'speaker', 'text', 'start', 'end' fields

    Returns:
        List of grouped chunks

    Example:
        >>> chunks = [
        ...     {'speaker': 'A', 'text': 'Hello', 'start': 0, 'end': 1},
        ...     {'speaker': 'A', 'text': 'world', 'start': 1, 'end': 2},
        ...     {'speaker': 'B', 'text': 'Hi', 'start': 2, 'end': 3},
        ... ]
        >>> grouped = group_by_speaker(chunks)
        >>> len(grouped)
        2
        >>> grouped[0]['text']
        'Hello world'
    """
    if not chunks:
        return []

    grouped = []
    current_speaker = None
    current_texts = []
    current_start = None
    current_end = None

    for chunk in chunks:
        speaker = chunk.get('speaker')
        text = chunk.get('text', '').strip()

        if not text:
            continue

        if speaker == current_speaker:
            # Same speaker, accumulate text
            current_texts.append(text)
            current_end = chunk.get('end', current_end)
        else:
            # New speaker, save previous group
            if current_texts:
                grouped.append({
                    'speaker': current_speaker,
                    'text': ' '.join(current_texts),
                    'start': current_start,
                    'end': current_end
                })

            # Start new group
            current_speaker = speaker
            current_texts = [text]
            current_start = chunk.get('start')
            current_end = chunk.get('end')

    # Add final group
    if current_texts:
        grouped.append({
            'speaker': current_speaker,
            'text': ' '.join(current_texts),
            'start': current_start,
            'end': current_end
        })

    logger.info(f"Grouped {len(chunks)} chunks into {len(grouped)} speaker segments")
    return grouped
