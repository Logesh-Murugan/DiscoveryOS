"""Report agent for compiling scored Themes into structured Report objects and Markdown reports."""

import logging
from datetime import datetime
from typing import List, Tuple, Dict, Optional
from uuid import uuid4

from app.models import Theme, PainPointUnit, Report

logger = logging.getLogger(__name__)


def generate_report(
    themes: List[Theme],
    pain_points: Optional[List[PainPointUnit]] = None,
) -> Tuple[Report, str]:
    """Generate a Report object and its Markdown representation.

    Args:
        themes: List of Theme objects, assumed to be sorted by priority descending.
        pain_points: Optional list of PainPointUnit objects. Required to render
            verbatim quotes, source IDs, and the count of sources analyzed.

    Returns:
        A tuple of (Report, markdown_string).
    """
    report_id = f"rep_{uuid4().hex[:8]}"
    generated_at = datetime.utcnow()
    theme_ids = [theme.id for theme in themes]

    # Initialize structured Report
    report = Report(
        id=report_id,
        generated_at=generated_at,
        theme_ids=theme_ids,
        version=1,
    )

    # Prepare pain point lookup and sources count
    pp_lookup: Dict[str, PainPointUnit] = {}
    sources_analyzed = set()
    total_pain_points = 0

    if pain_points:
        pp_lookup = {pp.id: pp for pp in pain_points}
        for pp in pain_points:
            if pp.source_id:
                sources_analyzed.add(pp.source_id)
        total_pain_points = len(pain_points)
    else:
        # Fallback if no pain_points list is supplied
        total_pain_points = sum(theme.frequency for theme in themes)

    # Build Markdown rendering
    md = []
    md.append("# Product Discovery Report")
    md.append(f"Generated at: {generated_at.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    md.append(f"Report ID: `{report_id}`  |  Version: `1`  ")
    md.append("\n## Executive Summary")
    md.append(f"- **Total Priority Themes**: {len(themes)}")
    md.append(f"- **Total Pain Points Extracted**: {total_pain_points}")
    md.append(f"- **Sources Analyzed**: {len(sources_analyzed) if pain_points else 'Unknown'}")
    md.append("\n" + "─" * 40 + "\n")

    md.append("## Identified Themes by Priority\n")

    for index, theme in enumerate(themes, 1):
        md.append(f"### {index}. {theme.label}")
        md.append(f"- **Priority Score**: `{theme.priority_score:.4f}`")
        md.append(f"- **Frequency**: {theme.frequency} occurrence(s)")
        
        # Segment breakdown
        segment_strs = [f"{seg}: {count}" for seg, count in theme.segment_breakdown.items()]
        md.append(f"- **Segment Breakdown**: {', '.join(segment_strs)}")
        
        # Recommendation
        md.append(f"- **Recommendation**: {theme.recommendation or 'N/A'}")
        
        # Verbatim quotes
        md.append("\n#### Supporting Verbatim Quotes:")
        has_quotes = False
        
        quote_list = []
        for pp_id in theme.pain_point_ids:
            pp = pp_lookup.get(pp_id)
            if pp:
                has_quotes = True
                # Escape any potential markdown formatting in quotes for safety
                escaped_quote = pp.verbatim_quote.replace("\n", " ").strip()
                quote_list.append(f"  - \"{escaped_quote}\" *(Source: `{pp.source_id}`)*")
        
        if has_quotes:
            md.append("<details>")
            md.append("<summary>Show supporting quotes</summary>\n")
            md.extend(quote_list)
            md.append("\n</details>")
        else:
            md.append("*No verbatim quotes available.*")
        
        md.append("\n" + "─" * 30 + "\n")

    markdown_str = "\n".join(md)
    return report, markdown_str
