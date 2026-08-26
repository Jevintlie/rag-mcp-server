try:
    from sentence_transformers.cross_encoder import CrossEncoder
except Exception:
    CrossEncoder = None

_rerank = None

def get_reranker(model_name="cross-encoder/ms-marco-MiniLM-L6-v2"):
    global _rerank
    if _rerank is None and CrossEncoder:
        _rerank = CrossEncoder(model_name)
    return _rerank

def rerank(query: str, candidates: list):
    """candidates = [{"text":..., "id":..., "metadata":...}, ...] -> sorted list"""
    model = get_reranker()
    if not model:
        return candidates  # no-op
    pairs = [[query, c["text"]] for c in candidates]
    scores = model.predict(pairs)
    for c, s in zip(candidates, scores): c["_score_rerank"] = float(s)
    return sorted(candidates, key=lambda x: x["_score_rerank"], reverse=True)
