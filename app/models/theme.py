"""Theme model for clustered pain points and their analysis."""

from typing import Dict
from pydantic import BaseModel, Field


class Theme(BaseModel):
    """Represents a clustered theme of related pain points.

    Attributes:
        id: Unique identifier for the theme.
        label: Human-readable name for the theme.
        pain_point_ids: List of pain point IDs included in this theme.
        segment_breakdown: Mapping of segment name to count of pain points in that segment.
        frequency: Total count of pain points in this theme.
        severity_score: Average severity score (0-1) for this theme.
        segment_value_score: Score indicating value/importance in specific segments (0-1).
        priority_score: Computed priority score combining frequency and severity.
        recommendation: Actionable recommendation based on this theme.
    """

    id: str = Field(..., description="Unique identifier for the theme")
    label: str = Field(..., description="Human-readable name for the theme")
    pain_point_ids: list[str] = Field(..., description="List of pain point IDs in this theme")
    segment_breakdown: Dict[str, int] = Field(
        ...,
        description="Mapping of segment name to count of pain points in that segment",
    )
    frequency: int = Field(..., ge=0, description="Total count of pain points in this theme")
    severity_score: float = Field(..., ge=0, le=1, description="Average severity score (0-1)")
    segment_value_score: float = Field(..., ge=0, le=1, description="Segment importance score (0-1)")
    priority_score: float = Field(..., description="Computed priority score")
    recommendation: str = Field(..., description="Actionable recommendation based on this theme")

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "id": "theme_001",
                "label": "Integration Complexity",
                "pain_point_ids": ["pp_001", "pp_002", "pp_003"],
                "segment_breakdown": {"Enterprise": 3, "SMB": 1, "Free": 0},
                "frequency": 4,
                "severity_score": 0.75,
                "segment_value_score": 0.85,
                "priority_score": 0.79,
                "recommendation": "Build native integrations for top 3 platforms",
            }
        }
