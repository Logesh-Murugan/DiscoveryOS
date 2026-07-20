"""Report model for aggregated analysis snapshots."""

from datetime import datetime
from pydantic import BaseModel, Field


class Report(BaseModel):
    """Represents a generated report snapshot of themes and analysis.

    Attributes:
        id: Unique identifier for the report.
        generated_at: Timestamp when the report was generated.
        theme_ids: List of theme IDs included in this report.
        version: Version number of the report (for tracking iterations).
    """

    id: str = Field(..., description="Unique identifier for the report")
    generated_at: datetime = Field(..., description="Timestamp when the report was generated")
    theme_ids: list[str] = Field(..., description="List of theme IDs included in this report")
    version: int = Field(..., ge=1, description="Version number of the report")

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "id": "report_001",
                "generated_at": "2024-01-20T14:30:00Z",
                "theme_ids": ["theme_001", "theme_002", "theme_003"],
                "version": 1,
            }
        }
