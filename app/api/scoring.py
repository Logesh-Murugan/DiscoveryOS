"""API routes for theme scoring and prioritization."""

from typing import Dict, List, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.agents.scoring_agent import score
from app.models import PainPointUnit, Theme

router = APIRouter(prefix="/score", tags=["scoring"])


class ScoreRequest(BaseModel):
    """Request body for the scoring endpoint.

    Attributes:
        themes: List of Theme objects to score.
        pain_points: Full list of PainPointUnit objects referenced by
            the themes.
        segment_weights: Optional custom segment value weights.
    """

    themes: List[Theme]
    pain_points: List[PainPointUnit]
    segment_weights: Optional[Dict[str, float]] = Field(
        None,
        description="Optional override for segment value weights. "
        'Defaults to {"Enterprise": 1.0, "SMB": 0.6, "Free": 0.3, "Unknown": 0.4}.',
    )


@router.post("/")
async def score_themes(request: ScoreRequest) -> JSONResponse:
    """Score and rank themes by priority.

    Accepts themes and their referenced pain points, computes severity,
    segment value, and priority scores, generates LLM recommendations,
    and returns themes sorted by priority descending.

    Args:
        request: ScoreRequest containing themes, pain points, and
            optional segment weights.

    Returns:
        JSON response with scored and sorted Theme objects.
    """
    try:
        scored = score(
            themes=request.themes,
            pain_points=request.pain_points,
            segment_weights=request.segment_weights,
        )
        scored_json = [theme.model_dump() for theme in scored]
        return JSONResponse({"status": "success", "themes": scored_json})
    except Exception as e:
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=400,
        )
