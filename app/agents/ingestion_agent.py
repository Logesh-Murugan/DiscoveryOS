"""Ingestion agent for normalizing raw feedback sources into Source objects."""

import csv
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from app.models import Source

logger = logging.getLogger(__name__)

# Lazy-loaded singleton instance for faster-whisper model
_whisper_model_cache = None


def _get_whisper_model():
    """Lazy load and return a faster-whisper WhisperModel instance."""
    global _whisper_model_cache
    if _whisper_model_cache is None:
        from faster_whisper import WhisperModel

        model_size = os.getenv("WHISPER_MODEL", "base")
        logger.info("Loading faster-whisper model: %s", model_size)
        # Run on CPU with int8 quantization for fast local transcription
        _whisper_model_cache = WhisperModel(model_size, device="cpu", compute_type="int8")
    return _whisper_model_cache


def ingest(file_paths: List[str]) -> List[Source]:
    """Ingest raw feedback files and normalize them into Source objects.

    Supports:
    - .txt files: treated as single transcript sources.
    - .csv files: each row treated as a separate source (survey or support_ticket).
    - .mp3, .wav files: transcribed via faster-whisper into an audio Source with timestamps.

    Args:
        file_paths: List of file paths to ingest.

    Returns:
        List of normalized Source objects.

    Raises:
        FileNotFoundError: If a file path does not exist.
        ValueError: If file type is unsupported.
    """
    sources: List[Source] = []

    for file_path in file_paths:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = path.suffix.lower()
        if ext == ".txt":
            sources.extend(_ingest_transcript(file_path))
        elif ext == ".csv":
            sources.extend(_ingest_csv(file_path))
        elif ext in (".mp3", ".wav"):
            sources.extend(_ingest_audio(file_path))
        else:
            raise ValueError(
                f"Unsupported file type: {ext}. Supported types: .txt, .csv, .mp3, .wav"
            )

    return sources


def _ingest_transcript(file_path: str) -> List[Source]:
    """Ingest a transcript file as a single Source.

    Args:
        file_path: Path to the .txt transcript file.

    Returns:
        List containing a single Source object.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        raw_content = f.read()

    source = Source(
        id=f"src_{uuid4().hex[:8]}",
        type="transcript",
        upload_date=datetime.utcnow(),
        raw_content=raw_content,
        segment="Unknown",
        use_case=None,
    )

    return [source]


_PREFERRED_CONTENT_COLUMNS = [
    "raw_content",
    "message",
    "text",
    "content",
    "comment",
    "feedback",
    "description",
]


def _detect_content_column(rows: List[dict], fieldnames: List[str], file_path: str) -> str:
    """Detect the free-text content column from CSV fieldnames or row heuristics.

    Priority:
    1. Exact match for 'raw_content'.
    2. Preferred names: 'message', 'text', 'content', 'comment', 'feedback', 'description'.
    3. Fallback: Column with the longest average string length across rows.

    Raises:
        ValueError: If no usable text column can be found, naming the columns that WERE found.
    """
    if not fieldnames:
        raise ValueError(f"CSV file is empty or missing a header row: {file_path}")

    # 1. Exact match for 'raw_content'
    if "raw_content" in fieldnames:
        return "raw_content"

    # Map lowercase stripped fieldname -> original fieldname
    fn_map = {fn.strip().lower(): fn for fn in fieldnames}

    # 2. Check preferred alternative names in priority order
    for col_name in _PREFERRED_CONTENT_COLUMNS:
        if col_name in fn_map:
            return fn_map[col_name]

    # 3. Fallback: Column with longest average string length
    if rows:
        col_avg_lengths = {}
        for fn in fieldnames:
            lengths = [len(str(row.get(fn, "") or "").strip()) for row in rows]
            avg_len = sum(lengths) / len(lengths) if lengths else 0
            col_avg_lengths[fn] = avg_len

        best_col = max(col_avg_lengths, key=col_avg_lengths.get)
        if col_avg_lengths[best_col] > 0:
            logger.info(
                "Inferred content column '%s' based on average text length (%.1f chars) for %s",
                best_col,
                col_avg_lengths[best_col],
                file_path,
            )
            return best_col

    # 4. Clear error naming which columns WERE found
    found_cols_str = ", ".join(f"'{fn}'" for fn in fieldnames)
    filename = Path(file_path).name
    raise ValueError(
        f"CSV file '{filename}' must contain a text content column (e.g. 'raw_content', 'message', 'text', 'content', 'comment', 'feedback', 'description'). "
        f"Columns found: [{found_cols_str}]."
    )


def _get_flexible_field(row: dict, candidates: List[str], default: str = "") -> str:
    """Case-insensitive lookup for optional fields in a CSV row dict."""
    row_map = {str(k).strip().lower(): str(v).strip() for k, v in row.items() if k and v}
    for cand in candidates:
        if cand.lower() in row_map:
            return row_map[cand.lower()]
    return default


def _ingest_csv(file_path: str) -> List[Source]:
    """Ingest a CSV file as multiple Source objects (one per row).

    Supports 'raw_content' or common alternatives ('message', 'text', 'content',
    'comment', 'feedback', 'description') or longest average string column fallback.

    Args:
        file_path: Path to the .csv file.

    Returns:
        List of Source objects, one per row.
    """
    sources: List[Source] = []

    # Use utf-8-sig to automatically strip BOM (\ufeff) if exported from Excel
    with open(file_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        if reader.fieldnames is None:
            return sources

        rows = list(reader)
        if not rows:
            return sources

        content_col = _detect_content_column(rows, list(reader.fieldnames), file_path)

        for row in rows:
            raw_text = (row.get(content_col) or "").strip()
            if not raw_text:
                continue

            segment = _get_flexible_field(
                row, ["segment", "customer_segment", "user_segment"], default="Unknown"
            )
            use_case = (
                _get_flexible_field(
                    row, ["use_case", "usecase", "industry", "category"], default=""
                )
                or None
            )
            source_type = _get_flexible_field(row, ["type", "source_type"], default="survey")

            source = Source(
                id=f"src_{uuid4().hex[:8]}",
                type=source_type if source_type in ("transcript", "survey", "support_ticket", "audio") else "survey",
                upload_date=datetime.utcnow(),
                raw_content=raw_text,
                segment=segment or "Unknown",
                use_case=use_case,
            )
            sources.append(source)

    return sources


def _ingest_audio(file_path: str) -> List[Source]:
    """Ingest an audio file (.mp3 / .wav) by transcribing it locally via faster-whisper.

    Embeds timestamps for each transcribed segment so downstream agents
    (e.g., extraction agent) can reference timestamps in quotes.

    Args:
        file_path: Path to the .mp3 or .wav file.

    Returns:
        List containing a single audio Source object.
    """
    model = _get_whisper_model()

    logger.info("Transcribing audio file: %s", file_path)
    segments, info = model.transcribe(file_path, beam_size=5)

    transcribed_lines = []
    for segment in segments:
        start_str = _format_timestamp(segment.start)
        end_str = _format_timestamp(segment.end)
        text = segment.text.strip()
        if text:
            transcribed_lines.append(f"[{start_str} - {end_str}] {text}")

    raw_content = "\n".join(transcribed_lines)

    source = Source(
        id=f"src_{uuid4().hex[:8]}",
        type="audio",
        upload_date=datetime.utcnow(),
        raw_content=raw_content,
        segment="Unknown",
        use_case=None,
    )

    return [source]


def _format_timestamp(seconds: float) -> str:
    """Format seconds into MM:SS or HH:MM:SS string."""
    total_seconds = int(seconds)
    m, s = divmod(total_seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"
