"""API routes for pain point clustering."""

from typing import List

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.agents.clustering_agent import cluster
from app.models import PainPointUnit, Theme

router = APIRouter(prefix="/cluster", tags=["clustering"])


@router.post("/")
async def cluster_pain_points(pain_points: List[PainPointUnit]) -> JSONResponse:
    """Cluster pain points into themes.

    Accepts a JSON array of PainPointUnit objects. Embeds and clusters them
    via HDBSCAN, then returns the resulting Theme objects with LLM-generated
    labels.

    Args:
        pain_points: List of PainPointUnit objects to cluster.

    Returns:
        JSON response with list of Theme objects.
    """
    try:
        themes: List[Theme] = cluster(pain_points)
        themes_json = [theme.model_dump() for theme in themes]
        return JSONResponse({"status": "success", "themes": themes_json})
    except Exception as e:
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=400,
        )
