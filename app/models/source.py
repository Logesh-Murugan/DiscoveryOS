"""Source model for documents/recordings that contain raw feedback."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Source(BaseModel):
    """Represents a source document or recording containing raw feedback.

    Attributes:
        id: Unique identifier for the source.
        type: Type of source (transcript, survey, support_ticket, or audio).
        upload_date: When the source was uploaded.
        raw_content: The original, unprocessed content.
        segment: Customer segment (e.g., "Enterprise", "SMB", "Free").
        use_case: Optional customer use case or industry.
    """

    id: str = Field(..., description="Unique identifier for the source")
    type: str = Field(
        ...,
        description="Type of source",
        pattern="^(transcript|survey|support_ticket|audio)$",
    )
    upload_date: datetime = Field(..., description="When the source was uploaded")
    raw_content: str = Field(..., description="Original, unprocessed content")
    segment: str = Field(..., description="Customer segment (e.g., Enterprise, SMB, Free)")
    use_case: Optional[str] = Field(None, description="Optional customer use case or industry")

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "id": "src_001",
                "type": "transcript",
                "upload_date": "2024-01-15T10:30:00Z",
                "raw_content": "Customer said they struggle with integration...",
                "segment": "Enterprise",
                "use_case": "SaaS",
            }
        }
