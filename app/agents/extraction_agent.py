"""Extraction agent for pulling atomic pain point units from a Source via LLM."""

import json
import logging
import re
from typing import List
from uuid import uuid4

from app.llm_client import get_llm_client
from app.models import PainPointUnit, Source

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a product-research analyst. Your job is to extract every \
distinct pain point from the provided customer feedback.

Return ONLY a JSON array (no markdown fences, no commentary). Each element must be an \
object with exactly these keys:

- "text": a single-sentence paraphrase of the pain point.
- "verbatim_quote": the EXACT substring from the original text that supports this \
pain point. Copy it character-for-character — do NOT paraphrase, fix grammar, or \
change punctuation.
- "sentiment": one of "mild", "moderate", or "severe".
- "use_case": a short label (1-3 words) describing what the user was trying to do \
when they hit this problem.

Rules:
1. Each pain point must be atomic — one problem per object.
2. verbatim_quote MUST appear verbatim in the source text. If you cannot find an \
exact supporting quote, do not include that pain point.
3. Return an empty array [] if there are no pain points.
"""

_USER_PROMPT_TEMPLATE = """Extract all pain points from the following customer feedback.

--- BEGIN FEEDBACK ---
{raw_content}
--- END FEEDBACK ---
"""


def extract(source: Source) -> List[PainPointUnit]:
    """Extract atomic pain point units from a Source using the LLM.

    Sends the source's raw_content to the configured LLM, parses the JSON
    response, validates verbatim quotes against the original text, and
    builds PainPointUnit objects from the validated results.

    Args:
        source: The Source object to extract pain points from.

    Returns:
        List of validated PainPointUnit objects.
    """
    client = get_llm_client()

    user_prompt = _USER_PROMPT_TEMPLATE.format(raw_content=source.raw_content)
    raw_response = client.generate(prompt=user_prompt, system=_SYSTEM_PROMPT)

    raw_items = _parse_llm_json(raw_response)

    pain_points: List[PainPointUnit] = []
    for item in raw_items:
        # --- Validate required keys ---
        if not isinstance(item, dict):
            logger.warning("Skipping non-dict item from LLM response: %s", item)
            continue

        text = item.get("text")
        verbatim_quote = item.get("verbatim_quote")
        sentiment = item.get("sentiment")
        use_case = item.get("use_case")

        if not all([text, verbatim_quote, sentiment, use_case]):
            logger.warning("Skipping item with missing fields: %s", item)
            continue

        # --- Validate sentiment value ---
        if sentiment not in ("mild", "moderate", "severe"):
            logger.warning(
                "Skipping item with invalid sentiment '%s': %s", sentiment, item
            )
            continue

        # --- Critical: verify verbatim_quote is a real substring ---
        if verbatim_quote not in source.raw_content:
            logger.warning(
                "Discarding pain point — verbatim_quote not found in source. "
                "Quote: %.80s...",
                verbatim_quote,
            )
            continue

        pain_point = PainPointUnit(
            id=f"pp_{uuid4().hex[:8]}",
            source_id=source.id,
            text=text,
            verbatim_quote=verbatim_quote,
            sentiment=sentiment,
            segment=source.segment,
            use_case=use_case,
        )
        pain_points.append(pain_point)

    logger.info(
        "Extracted %d validated pain points from source %s (discarded %d)",
        len(pain_points),
        source.id,
        len(raw_items) - len(pain_points),
    )

    return pain_points


def _parse_llm_json(raw_response: str) -> list:
    """Parse a JSON array from the LLM response, tolerating markdown fences.

    The LLM is instructed to return bare JSON, but may wrap it in
    ```json ... ``` fences anyway. This helper strips those before parsing.

    Args:
        raw_response: Raw text response from the LLM.

    Returns:
        Parsed list of dicts.

    Raises:
        ValueError: If the response cannot be parsed as a JSON array.
    """
    cleaned = raw_response.strip()

    # Strip markdown code fences if present
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", cleaned, re.DOTALL)
    if fence_match:
        cleaned = fence_match.group(1).strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"LLM did not return valid JSON. Raw response:\n{raw_response}"
        ) from exc

    if not isinstance(parsed, list):
        raise ValueError(
            f"Expected a JSON array from LLM, got {type(parsed).__name__}. "
            f"Raw response:\n{raw_response}"
        )

    return parsed
