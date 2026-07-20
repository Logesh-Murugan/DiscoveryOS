"""API routes for document ingestion."""

import shutil
import tempfile
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

from app.agents.ingestion_agent import ingest
from app.models import Source

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("/")
async def ingest_files(files: List[UploadFile] = File(...)) -> JSONResponse:
    """Ingest multiple files and return normalized Source objects.

    Accepts:
    - .txt files (transcripts)
    - .csv files (surveys, support tickets)
    - .mp3, .wav files (audio recordings transcribed via faster-whisper)

    Args:
        files: List of uploaded files.

    Returns:
        JSON response with list of Source objects.

    Raises:
        HTTPException: If file processing fails.
    """
    temp_dir = tempfile.mkdtemp()
    temp_paths: List[str] = []

    try:
        # Save uploaded files to temp directory
        for file in files:
            if file.filename is None:
                continue

            temp_path = Path(temp_dir) / file.filename
            with temp_path.open("wb") as f:
                content = await file.read()
                f.write(content)
            temp_paths.append(str(temp_path))

        # Ingest files
        sources = ingest(temp_paths)

        # Convert to JSON-serializable format
        sources_json = [source.model_dump() for source in sources]

        return JSONResponse({"status": "success", "sources": sources_json})

    except Exception as e:
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=400,
        )
    finally:
        # Clean up temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)
