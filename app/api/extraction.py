"""API routes for pain point extraction."""

from typing import List

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.agents.extraction_agent import extract
from app.models import PainPointUnit, Source

router = APIRouter(prefix="/extract", tags=["extraction"])


@router.post("/")
async def extract_pain_points(source: Source) -> JSONResponse:
    """Extract atomic pain point units from a Source object.

    Accepts a Source as a JSON body. The source's raw_content is sent to
    the LLM for pain point extraction, and the validated results are
    returned.

    Args:
        source: The Source object to extract pain points from.

    Returns:
        JSON response with list of PainPointUnit objects.
    """
    try:
        pain_points: List[PainPointUnit] = extract(source)
        pain_points_json = [pp.model_dump() for pp in pain_points]
        return JSONResponse(
            {"status": "success", "pain_points": pain_points_json}
        )
    except Exception as e:
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=400,
        )
