"""Clustering agent for grouping PainPointUnits into Themes via embeddings + HDBSCAN."""

import logging
from collections import Counter
from typing import Dict, List
from uuid import uuid4

import hdbscan
import numpy as np
from sentence_transformers import SentenceTransformer

from app.llm_client import get_llm_client
from app.models import PainPointUnit, Theme

logger = logging.getLogger(__name__)

_EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Lazy-loaded singleton so the model is only downloaded / loaded once.
_model_cache: SentenceTransformer | None = None


def _get_embedding_model() -> SentenceTransformer:
    """Return a cached SentenceTransformer instance.

    Returns:
        A SentenceTransformer model for encoding pain point texts.
    """
    global _model_cache
    if _model_cache is None:
        logger.info("Loading sentence-transformers model: %s", _EMBEDDING_MODEL)
        _model_cache = SentenceTransformer(_EMBEDDING_MODEL)
    return _model_cache


def cluster(pain_points: List[PainPointUnit]) -> List[Theme]:
    """Cluster a list of PainPointUnits into Themes.

    Pipeline:
    1. Embed each pain point's ``text`` field with sentence-transformers.
    2. Cluster the embeddings with HDBSCAN (min_cluster_size=2).
    3. For real clusters, ask the LLM to generate a human-readable label.
    4. Noise points (label == -1) become singleton themes flagged as
       low-confidence.

    Args:
        pain_points: List of PainPointUnit objects to cluster.

    Returns:
        List of Theme objects, one per cluster plus one per noise point.
    """
    if not pain_points:
        return []

    # --- 1. Embed ---
    model = _get_embedding_model()
    texts = [pp.text for pp in pain_points]
    embeddings = model.encode(texts, show_progress_bar=False)

    # --- 2. Cluster ---
    # Sentence-transformer embeddings are high-dimensional (384-d).
    # Euclidean distance in that space is uninformative for small datasets,
    # so we pre-compute a cosine distance matrix and pass it to HDBSCAN.
    from sklearn.metrics.pairwise import cosine_distances

    distance_matrix = cosine_distances(embeddings).astype(np.float64)

    # For very small datasets (< min_cluster_size) HDBSCAN marks everything
    # as noise, which is fine — they'll become singleton themes.
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=2,
        min_samples=1,
        metric="precomputed",
    )
    labels = clusterer.fit_predict(distance_matrix)

    # --- 3. Group pain points by cluster label ---
    cluster_map: Dict[int, List[int]] = {}
    for idx, label in enumerate(labels):
        cluster_map.setdefault(int(label), []).append(idx)

    # --- 4. Build themes ---
    llm = get_llm_client()
    themes: List[Theme] = []

    # Process real clusters first (label >= 0), then noise (label == -1)
    for cluster_label in sorted(cluster_map.keys(), reverse=True):
        member_indices = cluster_map[cluster_label]
        members = [pain_points[i] for i in member_indices]

        is_noise = cluster_label == -1

        if is_noise:
            # Each noise point becomes its own singleton theme
            for member in members:
                theme = _build_singleton_theme(member)
                themes.append(theme)
        else:
            theme = _build_cluster_theme(members, llm)
            themes.append(theme)

    logger.info(
        "Clustered %d pain points into %d themes (%d real clusters, %d singletons)",
        len(pain_points),
        len(themes),
        sum(1 for lbl in cluster_map if lbl >= 0),
        sum(1 for lbl in cluster_map if lbl == -1) and len(cluster_map.get(-1, [])),
    )

    return themes


def _build_cluster_theme(members: List[PainPointUnit], llm) -> Theme:
    """Build a Theme from a real HDBSCAN cluster.

    Uses the LLM to generate a human-readable label from the member texts.

    Args:
        members: PainPointUnit objects belonging to this cluster.
        llm: An LLMClient instance for label generation.

    Returns:
        A Theme object representing the cluster.
    """
    label = _generate_theme_label(members, llm)
    segment_breakdown = _compute_segment_breakdown(members)

    return Theme(
        id=f"theme_{uuid4().hex[:8]}",
        label=label,
        pain_point_ids=[m.id for m in members],
        segment_breakdown=segment_breakdown,
        frequency=len(members),
        # Placeholder scores — the scoring agent fills these in later.
        severity_score=0.0,
        segment_value_score=0.0,
        priority_score=0.0,
        recommendation="",
    )


def _build_singleton_theme(member: PainPointUnit) -> Theme:
    """Build a singleton Theme for a noise-point pain point.

    These are pain points HDBSCAN couldn't assign to any cluster.
    They are kept rather than dropped, but flagged via a label prefix.

    Args:
        member: The single PainPointUnit.

    Returns:
        A singleton Theme flagged as low-confidence.
    """
    segment_breakdown = _compute_segment_breakdown([member])

    return Theme(
        id=f"theme_{uuid4().hex[:8]}",
        label=f"[Low-confidence] {member.text}",
        pain_point_ids=[member.id],
        segment_breakdown=segment_breakdown,
        frequency=1,
        # Placeholder scores — the scoring agent fills these in later.
        severity_score=0.0,
        segment_value_score=0.0,
        priority_score=0.0,
        recommendation="",
    )


def _compute_segment_breakdown(members: List[PainPointUnit]) -> Dict[str, int]:
    """Count pain points per segment within a group.

    Args:
        members: PainPointUnit objects in the group.

    Returns:
        Dict mapping segment name to count.
    """
    return dict(Counter(m.segment for m in members))


def _generate_theme_label(members: List[PainPointUnit], llm) -> str:
    """Ask the LLM to generate a short label for a cluster of pain points.

    Args:
        members: PainPointUnit objects in the cluster.
        llm: An LLMClient instance.

    Returns:
        A concise theme label string.
    """
    bullet_list = "\n".join(f"- {m.text}" for m in members)
    prompt = (
        "Below are several related customer pain points that were grouped together.\n"
        "Generate a short, human-readable label (3-6 words) that summarizes the\n"
        "common theme. Return ONLY the label text, nothing else.\n\n"
        f"{bullet_list}"
    )
    label = llm.generate(prompt=prompt, system="You are a concise labelling assistant.")
    # Strip quotes / whitespace the LLM might add
    return label.strip().strip('"').strip("'")
