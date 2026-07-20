"""Test script: exercises the clustering pipeline with enough data to form real clusters.

When Ollama is not running, patches the LLM to use a simple fallback label
so the clustering + noise handling can be fully demonstrated.
"""

import logging
import sys
import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

logging.basicConfig(level=logging.INFO, format="%(name)s | %(levelname)s | %(message)s")

from app.models import PainPointUnit

test_pain_points = [
    # -- Cluster A: Bulk operations (4 related points) --
    PainPointUnit(
        id="pp_bulk_01", source_id="src_001",
        text="Bulk export times out when exporting more than 100k records",
        verbatim_quote="bulk export times out", sentiment="severe",
        segment="Enterprise", use_case="Data Export",
    ),
    PainPointUnit(
        id="pp_bulk_02", source_id="src_002",
        text="No bulk delete feature forces manual one-by-one record deletion",
        verbatim_quote="manually delete records one at a time", sentiment="moderate",
        segment="SMB", use_case="Data Management",
    ),
    PainPointUnit(
        id="pp_bulk_03", source_id="src_003",
        text="Bulk import fails silently when CSV has more than 50k rows",
        verbatim_quote="bulk import fails silently", sentiment="severe",
        segment="Enterprise", use_case="Data Import",
    ),
    PainPointUnit(
        id="pp_bulk_04", source_id="src_004",
        text="Bulk user provisioning is missing so admins add users one at a time",
        verbatim_quote="add users one at a time", sentiment="moderate",
        segment="Enterprise", use_case="User Management",
    ),
    # -- Cluster B: API / integration (3 related points) --
    PainPointUnit(
        id="pp_api_01", source_id="src_005",
        text="API rate limiting forces developers to stagger batch operations over 3 hours",
        verbatim_quote="stagger it over 3 hours", sentiment="severe",
        segment="Enterprise", use_case="API Integration",
    ),
    PainPointUnit(
        id="pp_api_02", source_id="src_006",
        text="No API documentation for analytics endpoints makes integration difficult",
        verbatim_quote="no API documentation", sentiment="moderate",
        segment="SMB", use_case="API Integration",
    ),
    PainPointUnit(
        id="pp_api_03", source_id="src_007",
        text="API error responses lack detail making debugging integrations very hard",
        verbatim_quote="error responses lack detail", sentiment="moderate",
        segment="SMB", use_case="API Debugging",
    ),
    # -- Outlier: completely different topic --
    PainPointUnit(
        id="pp_dark_01", source_id="src_008",
        text="No dark mode causes eye strain for teams working late nights",
        verbatim_quote="bright UI causes eye strain", sentiment="mild",
        segment="SMB", use_case="UI Customization",
    ),
]


def _try_ollama():
    """Check if Ollama is reachable."""
    import requests
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=2)
        return resp.status_code == 200
    except Exception:
        return False


class FallbackLLM:
    """Simple fallback that generates a label from the first few words of each member."""
    def generate(self, prompt: str, system: str = "") -> str:
        # Extract the bullet lines from the prompt
        lines = [l.strip("- ").strip() for l in prompt.split("\n") if l.strip().startswith("-")]
        if not lines:
            return "Miscellaneous"
        # Find common words
        word_sets = [set(line.lower().split()) for line in lines]
        common = word_sets[0]
        for ws in word_sets[1:]:
            common &= ws
        # Remove stopwords
        stopwords = {"the", "a", "an", "is", "are", "for", "to", "and", "of", "in", "that", "it", "when", "so", "no"}
        common -= stopwords
        if common:
            return " ".join(sorted(common)[:4]).title() + " Issues"
        # Fallback: use first 4 words of first line
        return " ".join(lines[0].split()[:4]) + "..."


def main():
    print("=" * 70)
    print("CLUSTERING TEST -- 8 pain points")
    print("  Expected: ~2 real clusters + 1 singleton")
    print("=" * 70)

    print(f"\nInput: {len(test_pain_points)} pain points")
    for pp in test_pain_points:
        print(f"  [{pp.id}] ({pp.segment}) {pp.text}")

    # Check if Ollama is running
    ollama_ok = _try_ollama()
    if ollama_ok:
        print("\n  [LLM] Ollama is running -- will use real LLM for theme labels")
    else:
        print("\n  [LLM] Ollama not running -- using fallback label generator")
        # Patch get_llm_client to return our fallback
        import app.agents.clustering_agent as ca
        _original_get_llm = ca.get_llm_client
        ca.get_llm_client = lambda: FallbackLLM()

    print("\n--- Running clustering pipeline ---\n")
    try:
        from app.agents.clustering_agent import cluster
        themes = cluster(test_pain_points)
    except Exception as e:
        print(f"ERROR during clustering: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print(f"\n{'=' * 70}")
    print(f"OUTPUT: {len(themes)} themes")
    print(f"{'=' * 70}")

    real_clusters = []
    singletons = []

    for theme in themes:
        is_singleton = theme.label.startswith("[Low-confidence]")
        if is_singleton:
            singletons.append(theme)
        else:
            real_clusters.append(theme)

        print(f"\n  Theme: {theme.label}")
        print(f"  ID: {theme.id}")
        print(f"  Frequency: {theme.frequency}")
        print(f"  Segment breakdown: {theme.segment_breakdown}")
        print(f"  Pain point IDs: {theme.pain_point_ids}")
        if is_singleton:
            print(f"  ** SINGLETON (HDBSCAN noise) -- kept, not dropped")
        else:
            print(f"  Member texts that generated this label:")
            for pid in theme.pain_point_ids:
                member = next(pp for pp in test_pain_points if pp.id == pid)
                print(f"    - {member.text}")

    print(f"\n{'=' * 70}")
    print(f"SUMMARY")
    print(f"  Total pain points in:  {len(test_pain_points)}")
    print(f"  Total themes out:      {len(themes)}")
    print(f"  Real clusters:         {len(real_clusters)}")
    print(f"  Singletons (noise):    {len(singletons)}")

    all_output_ids = set()
    for t in themes:
        all_output_ids.update(t.pain_point_ids)
    all_input_ids = {pp.id for pp in test_pain_points}
    dropped = all_input_ids - all_output_ids
    print(f"  Dropped pain points:   {len(dropped)}")
    if dropped:
        print(f"    DROPPED IDs: {dropped}")
    else:
        print(f"    OK -- No pain points were dropped -- all accounted for!")

    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
