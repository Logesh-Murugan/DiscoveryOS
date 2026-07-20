"""Scoring agent for computing severity, segment value, and priority scores on Themes.

All formula weights are declared as named constants at the top of this file
so they are easy to find, audit, and change.
"""

import logging
from typing import Dict, List, Optional

from app.llm_client import get_llm_client
from app.models import PainPointUnit, Theme

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════
# SCORING FORMULA WEIGHTS — edit these to tune the scoring model
# ══════════════════════════════════════════════════════════════════════

# Severity: how much each sentiment level contributes (0-1 scale)
SENTIMENT_WEIGHTS: Dict[str, float] = {
    "severe": 1.0,
    "moderate": 0.6,
    "mild": 0.3,
}

# Segment value: how much each customer segment is worth (0-1 scale)
DEFAULT_SEGMENT_WEIGHTS: Dict[str, float] = {
    "Enterprise": 1.0,
    "SMB": 0.6,
    "Free": 0.3,
    "Unknown": 0.4,
}

# Priority score: relative importance of each component (must sum to 1.0)
PRIORITY_WEIGHT_FREQUENCY: float = 0.40
PRIORITY_WEIGHT_SEGMENT: float = 0.35
PRIORITY_WEIGHT_SEVERITY: float = 0.25


def score(
    themes: List[Theme],
    pain_points: List[PainPointUnit],
    segment_weights: Optional[Dict[str, float]] = None,
) -> List[Theme]:
    """Score and rank a list of Themes by priority.

    Computes severity_score, segment_value_score, priority_score, and an
    LLM-generated recommendation for each Theme, then returns the list
    sorted by priority_score descending.

    Args:
        themes: Themes with pain_point_ids, segment_breakdown, and
            frequency already populated (e.g. from the clustering agent).
        pain_points: The full list of PainPointUnit objects referenced by
            the themes (used to look up sentiment values).
        segment_weights: Optional override for segment value weights.
            Defaults to DEFAULT_SEGMENT_WEIGHTS.

    Returns:
        A new list of Theme objects with all scoring fields filled in,
        sorted by priority_score descending.
    """
    if not themes:
        return []

    weights = segment_weights or DEFAULT_SEGMENT_WEIGHTS

    # Build a lookup for quick access to pain points by ID
    pp_lookup: Dict[str, PainPointUnit] = {pp.id: pp for pp in pain_points}

    # Compute the max frequency across all themes for normalization
    max_frequency = max(theme.frequency for theme in themes)

    llm = get_llm_client()

    scored_themes: List[Theme] = []
    for theme in themes:
        # --- 1. Severity score ---
        severity = _compute_severity_score(theme, pp_lookup)

        # --- 2. Segment value score ---
        segment_value = _compute_segment_value_score(theme, weights)

        # --- 3. Priority score ---
        normalized_freq = theme.frequency / max_frequency if max_frequency > 0 else 0.0
        priority = (
            PRIORITY_WEIGHT_FREQUENCY * normalized_freq
            + PRIORITY_WEIGHT_SEGMENT * segment_value
            + PRIORITY_WEIGHT_SEVERITY * severity
        )

        # --- 4. Recommendation ---
        recommendation = _generate_recommendation(theme, severity, segment_value, priority, llm)

        # Build a new Theme with scores filled in (Theme is immutable-ish via Pydantic)
        scored_theme = theme.model_copy(
            update={
                "severity_score": round(severity, 4),
                "segment_value_score": round(segment_value, 4),
                "priority_score": round(priority, 4),
                "recommendation": recommendation,
            }
        )
        scored_themes.append(scored_theme)

    # --- 5. Sort by priority descending ---
    scored_themes.sort(key=lambda t: t.priority_score, reverse=True)

    logger.info(
        "Scored %d themes. Top theme: '%s' (priority=%.4f)",
        len(scored_themes),
        scored_themes[0].label if scored_themes else "N/A",
        scored_themes[0].priority_score if scored_themes else 0.0,
    )

    return scored_themes


# ══════════════════════════════════════════════════════════════════════
# Internal scoring helpers
# ══════════════════════════════════════════════════════════════════════


def _compute_severity_score(
    theme: Theme,
    pp_lookup: Dict[str, PainPointUnit],
) -> float:
    """Compute the average severity score for a theme's pain points.

    Each pain point's sentiment is mapped to a numeric weight via
    SENTIMENT_WEIGHTS, then averaged.

    Args:
        theme: The Theme to score.
        pp_lookup: Mapping of pain point ID to PainPointUnit.

    Returns:
        A float in [0, 1].
    """
    scores: List[float] = []
    for pp_id in theme.pain_point_ids:
        pp = pp_lookup.get(pp_id)
        if pp is None:
            logger.warning("Pain point %s not found in lookup, skipping", pp_id)
            continue
        scores.append(SENTIMENT_WEIGHTS.get(pp.sentiment, 0.3))

    if not scores:
        return 0.0
    return sum(scores) / len(scores)


def _compute_segment_value_score(
    theme: Theme,
    weights: Dict[str, float],
) -> float:
    """Compute the weighted average segment value for a theme.

    Each segment in the theme's segment_breakdown contributes its weight
    multiplied by the number of pain points from that segment. The result
    is normalized by total pain point count.

    Args:
        theme: The Theme to score.
        weights: Mapping of segment name to value weight.

    Returns:
        A float in [0, 1].
    """
    total_count = sum(theme.segment_breakdown.values())
    if total_count == 0:
        return 0.0

    weighted_sum = 0.0
    for segment, count in theme.segment_breakdown.items():
        segment_weight = weights.get(segment, weights.get("Unknown", 0.4))
        weighted_sum += segment_weight * count

    return weighted_sum / total_count


def _generate_recommendation(
    theme: Theme,
    severity: float,
    segment_value: float,
    priority: float,
    llm,
) -> str:
    """Generate a single-sentence PM recommendation for a theme.

    Args:
        theme: The Theme to generate a recommendation for.
        severity: The computed severity score.
        segment_value: The computed segment value score.
        priority: The computed priority score.
        llm: An LLMClient instance.

    Returns:
        A single-sentence recommendation string.
    """
    segments_str = ", ".join(
        f"{seg} ({count})" for seg, count in theme.segment_breakdown.items()
    )

    prompt = (
        f"Theme: \"{theme.label}\"\n"
        f"Affected segments: {segments_str}\n"
        f"Frequency: {theme.frequency} pain points\n"
        f"Severity score: {severity:.2f}/1.0\n"
        f"Segment value score: {segment_value:.2f}/1.0\n"
        f"Priority score: {priority:.2f}/1.0\n\n"
        "Write ONE actionable sentence a product manager should consider "
        "doing about this theme. Be specific and practical. "
        "Return ONLY the recommendation sentence, nothing else."
    )

    system = "You are a product strategy advisor. Be concise and actionable."

    try:
        recommendation = llm.generate(prompt=prompt, system=system)
        return recommendation.strip().strip('"')
    except Exception as e:
        logger.warning("LLM recommendation failed for theme '%s': %s", theme.label, e)
        return f"Review theme \"{theme.label}\" (priority {priority:.2f}) with the product team."
