"""QA agent for answering natural-language questions about generated reports."""

import logging
from typing import Dict, List, Any
from app.llm_client import get_llm_client
from app.models import Theme, PainPointUnit

logger = logging.getLogger(__name__)

# Simple in-memory database to store report contexts
# Key: report_id (str)
# Value: dict containing:
#   - "themes": List[Theme]
#   - "pain_points": List[PainPointUnit]
REPORT_STORE: Dict[str, Dict[str, Any]] = {}


def save_report_data(
    report_id: str,
    themes: List[Theme],
    pain_points: List[PainPointUnit],
) -> None:
    """Store theme and pain point data for a generated report.

    Args:
        report_id: The ID of the report.
        themes: Scored Themes included in the report.
        pain_points: PainPointUnits referenced by the report.
    """
    REPORT_STORE[report_id] = {
        "themes": themes,
        "pain_points": pain_points,
    }
    logger.info("Saved report data to store for report ID: %s", report_id)


def answer_question(report_id: str, question: str) -> str:
    """Answer questions about a generated report using LLM and context.

    Builds context from stored themes and pain points, matching keywords from
    the question if the data is large, and sends it to the LLM for answering.

    Args:
        report_id: The ID of the report.
        question: The natural-language question.

    Returns:
        The text answer from the LLM.

    Raises:
        ValueError: If the report ID is not found in the store.
    """
    if report_id not in REPORT_STORE:
        raise ValueError(f"Report ID '{report_id}' not found in the QA store.")

    data = REPORT_STORE[report_id]
    themes: List[Theme] = data["themes"]
    pain_points: List[PainPointUnit] = data["pain_points"]

    # 1. Build context
    # If the report is large, we can filter by simple keyword match to avoid context limits.
    # Otherwise, we include the entire theme and pain point set.
    context_str = _build_context(themes, pain_points, question)

    # 2. Invoke LLM
    llm = get_llm_client()

    system_prompt = (
        "You are an expert product analyst answering user questions about a user feedback discovery report.\n"
        "Use ONLY the provided report context to answer the user's question. Do not make up facts or extrapolate.\n"
        "If the answer is not supported by or found in the context, respond exactly with:\n"
        "\"I don't have that information in this report.\""
    )

    user_prompt = (
        f"--- BEGIN REPORT CONTEXT ---\n{context_str}\n--- END REPORT CONTEXT ---\n\n"
        f"Question: {question}\n"
        "Answer:"
    )

    return llm.generate(prompt=user_prompt, system=system_prompt)


def _build_context(
    themes: List[Theme],
    pain_points: List[PainPointUnit],
    question: str,
) -> str:
    """Compile themes and pain points into a context string, optionally filtering by keyword if large."""
    pp_lookup = {pp.id: pp for pp in pain_points}
    
    # We define a simple threshold for filtering. If we have more than 15 pain points, filter context.
    # If the question is short or empty, or if we are under the threshold, return everything.
    words = [w.lower() for w in question.split() if len(w) > 3]
    should_filter = len(pain_points) > 15 and len(words) > 0

    lines = []
    
    # Add summary statistics
    lines.append(f"Total themes: {len(themes)}")
    lines.append(f"Total pain points: {len(pain_points)}")
    lines.append("")

    for index, theme in enumerate(themes, 1):
        # Check if the theme or its member pain points match the question keywords
        theme_matches = True
        if should_filter:
            # Check theme label match
            label_match = any(word in theme.label.lower() for word in words)
            # Check member pain points text match
            member_match = False
            for pid in theme.pain_point_ids:
                pp = pp_lookup.get(pid)
                if pp and any(word in pp.text.lower() for word in words):
                    member_match = True
                    break
            theme_matches = label_match or member_match

        if not theme_matches:
            continue

        lines.append(f"Theme {index}: {theme.label} (Priority Score: {theme.priority_score:.4f}, Frequency: {theme.frequency})")
        lines.append(f"Recommendation: {theme.recommendation}")
        lines.append(f"Segment breakdown: {theme.segment_breakdown}")
        lines.append("Supporting verbatim quotes:")
        
        for pid in theme.pain_point_ids:
            pp = pp_lookup.get(pid)
            if pp:
                lines.append(f"  - \"{pp.verbatim_quote}\" (Segment: {pp.segment}, Use Case: {pp.use_case}, Sentiment: {pp.sentiment})")
        lines.append("")

    context = "\n".join(lines).strip()
    # In case filtering was too aggressive and returned nothing, fallback to complete context.
    if not context:
        return _build_context(themes, pain_points, "")
        
    return context
