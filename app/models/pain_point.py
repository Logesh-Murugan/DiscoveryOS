"""Pain point model for extracted and structured feedback units."""

from typing import Optional
from pydantic import BaseModel, Field


class PainPointUnit(BaseModel):
    """Represents an extracted, paraphrased pain point from a source.

    Attributes:
        id: Unique identifier for this pain point.
        source_id: Reference to the source it came from.
        text: Paraphrased/cleaned version of the pain point.
        verbatim_quote: Exact quote from the source.
        timestamp: Optional timestamp (relevant for audio sources).
        sentiment: Severity level of the pain point.
        segment: Customer segment affected by this pain point.
        use_case: The use case associated with this pain point.
    """

    id: str = Field(..., description="Unique identifier for this pain point")
    source_id: str = Field(..., description="Reference to the source it came from")
    text: str = Field(..., description="Paraphrased/cleaned version of the pain point")
    verbatim_quote: str = Field(..., description="Exact quote from the source")
    timestamp: Optional[str] = Field(None, description="Optional timestamp (e.g., for audio sources)")
    sentiment: str = Field(
        ...,
        description="Severity level of the pain point",
        pattern="^(mild|moderate|severe)$",
    )
    segment: str = Field(..., description="Customer segment affected by this pain point")
    use_case: str = Field(..., description="The use case associated with this pain point")

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "id": "pp_001",
                "source_id": "src_001",
                "text": "Integration with third-party tools is time-consuming",
                "verbatim_quote": "It takes forever to integrate with our existing tools",
                "timestamp": "00:05:23",
                "sentiment": "moderate",
                "segment": "Enterprise",
                "use_case": "SaaS",
            }
        }
