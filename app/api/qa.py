"""API routes for Q&A on generated reports."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.agents.qa_agent import answer_question

router = APIRouter(prefix="/report", tags=["qa"])


class AskRequest(BaseModel):
    """Request body for the report Q&A endpoint.

    Attributes:
        question: Natural-language question about the report.
    """

    question: str = Field(..., description="Natural-language question about the report")


@router.post("/{report_id}/ask")
async def ask_report_question(
    report_id: str,
    request: AskRequest,
) -> JSONResponse:
    """Ask a natural-language question about a generated report.

    Finds the stored report context, builds relevant cues, and uses the LLM
    to generate an answer constrained strictly to the report data.

    Args:
        report_id: The ID of the report to query.
        request: The AskRequest containing the question.

    Returns:
        JSON response with the answer.
    """
    try:
        answer = answer_question(report_id, request.question)
        return JSONResponse({"status": "success", "answer": answer})
    except ValueError as e:
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=404,
        )
    except Exception as e:
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=400,
        )
