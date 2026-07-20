"""API routes for end-to-end report generation."""

import logging
import shutil
import tempfile
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

from app.agents.ingestion_agent import ingest
from app.agents.extraction_agent import extract
from app.agents.clustering_agent import cluster
from app.agents.scoring_agent import score
from app.agents.report_agent import generate_report
from app.agents.qa_agent import save_report_data

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/report", tags=["report"])


@router.post("/generate")
async def generate_pipeline_report(
    files: List[UploadFile] = File(...),
) -> JSONResponse:
    """Run the end-to-end discovery pipeline on uploaded files.

    Pipeline stages:
    1. Ingest: Saves uploaded files and normalizes them to Source objects.
    2. Extract: Sends raw content of each source to the LLM to extract PainPointUnits.
    3. Cluster: Sentence-embeddings + HDBSCAN to group pain points into Themes.
    4. Score: Computes severity, segment value, priority, and recommendation for themes.
    5. Report: Compiles themes and pain points into a structured Report and Markdown.

    Returns:
        JSON response with the structured Report and the rendered Markdown.
    """
    temp_dir = tempfile.mkdtemp()
    temp_paths: List[str] = []

    try:
        # --- STAGE 1: INGESTION (Saving files) ---
        try:
            for file in files:
                if not file.filename:
                    continue
                temp_path = Path(temp_dir) / file.filename
                with temp_path.open("wb") as f:
                    content = await file.read()
                    f.write(content)
                temp_paths.append(str(temp_path))
            
            sources = ingest(temp_paths)
        except Exception as e:
            return JSONResponse(
                {"status": "error", "stage": "Ingestion", "message": f"Ingestion stage failed: {e}"},
                status_code=400,
            )

        # --- STAGE 2: EXTRACTION ---
        pain_points = []
        try:
            for source in sources:
                extracted = extract(source)
                pain_points.extend(extracted)
        except Exception as e:
            return JSONResponse(
                {"status": "error", "stage": "Extraction", "message": f"Extraction stage failed: {e}"},
                status_code=400,
            )

        if not pain_points:
            return JSONResponse(
                {
                    "status": "error",
                    "stage": "Extraction",
                    "message": "No pain points were successfully extracted from the sources. Cannot proceed.",
                },
                status_code=400,
            )

        # --- STAGE 3: CLUSTERING ---
        try:
            themes = cluster(pain_points)
        except Exception as e:
            return JSONResponse(
                {"status": "error", "stage": "Clustering", "message": f"Clustering stage failed: {e}"},
                status_code=400,
            )

        # --- STAGE 4: SCORING ---
        try:
            scored_themes = score(themes, pain_points)
        except Exception as e:
            return JSONResponse(
                {"status": "error", "stage": "Scoring", "message": f"Scoring stage failed: {e}"},
                status_code=400,
            )

        # --- STAGE 5: REPORT GENERATION ---
        try:
            report_obj, report_md = generate_report(scored_themes, pain_points)
        except Exception as e:
            return JSONResponse(
                {"status": "error", "stage": "Report Generation", "message": f"Report generation stage failed: {e}"},
                status_code=400,
            )

        # Store report data in-memory for Q&A query capability
        try:
            save_report_data(report_obj.id, scored_themes, pain_points)
        except Exception as e:
            logger.warning("Failed to store report data for Q&A: %s", e)

        return JSONResponse(
            {
                "status": "success",
                "report": report_obj.model_dump(),
                "themes": [theme.model_dump() for theme in scored_themes],
                "pain_points": [pp.model_dump() for pp in pain_points],
                "markdown": report_md,
            }
        )

    finally:
        # Cleanup temp upload directory
        shutil.rmtree(temp_dir, ignore_errors=True)
