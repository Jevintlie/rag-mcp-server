from sentence_transformers import SentenceTransformer

_model = None

def get_embedder(model_name: str):
    global _model
    if _model is None:
        _model = SentenceTransformer(model_name)  # all-MiniLM-L6-v2 (384-d)
    return _model

def encode(texts, convert_to_numpy=True):
    return get_embedder("sentence-transformers/all-MiniLM-L6-v2").encode(
        texts, normalize_embeddings=True, convert_to_numpy=convert_to_numpy
    )
