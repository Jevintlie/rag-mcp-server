# src/rag_mcp/index/reranker.py

from typing import List, Dict, Any, Optional

try:
    from sentence_transformers.cross_encoder import CrossEncoder
except Exception:
    # CrossEncoder not available (package missing or import error)
    CrossEncoder = None  # type: ignore[assignment]

from ..config import RERANK_MODEL

_rerank_model: Optional["CrossEncoder"] = None  # type: ignore[name-defined]


def get_reranker(model_name: Optional[str] = None) -> "CrossEncoder":
    """
    Lazily create and cache a CrossEncoder for reranking.

    Strictly offline:
      - Uses local_files_only=True, so it will only load from a local folder
        or local HF cache and never attempt to download from the internet.

    Raises:
      RuntimeError if CrossEncoder is unavailable or the local model
      cannot be loaded.
    """
    global _rerank_model

    if _rerank_model is not None:
        return _rerank_model

    if CrossEncoder is None:
        raise RuntimeError(
            "[RAG] sentence-transformers CrossEncoder is not available. "
            "Install sentence-transformers with cross-encoder support."
        )

    name = model_name or RERANK_MODEL

    try:
        _rerank_model = CrossEncoder(name, local_files_only=True)
    except Exception as e:
        raise RuntimeError(
            f"[RAG] Failed to load reranker model from '{name}'. "
            f"Make sure the folder exists and contains a valid CrossEncoder model "
            f"(e.g. models/ms-marco-MiniLM-L6-v2)."
        ) from e

    return _rerank_model


def rerank(query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Rerank candidates by relevance to the query using the CrossEncoder.

    Args:
      query: User query string.
      candidates: List of docs with at least a "text" field:
        [{"text": ..., "id": ..., "metadata": ...}, ...]

    Returns:
      The same list, sorted by rerank score (highest first), with
      an extra "_score_rerank" field on each candidate.
    """
    if not candidates:
        return candidates

    model = get_reranker()

    pairs = [[query, c["text"]] for c in candidates]
    scores = model.predict(pairs)

    for c, s in zip(candidates, scores):
        c["_score_rerank"] = float(s)

    return sorted(candidates, key=lambda x: x["_score_rerank"], reverse=True)
