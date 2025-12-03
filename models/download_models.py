# download_models.py
from pathlib import Path
from sentence_transformers import SentenceTransformer, CrossEncoder

def main():
    base = Path(__file__).resolve().parent  # this will be the "models" folder
    embed_path = base / "all-MiniLM-L6-v2"
    rerank_path = base / "ms-marco-MiniLM-L6-v2"

    # Download/embedder model
    if not embed_path.exists():
        print("Downloading embedder →", embed_path)
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        model.save(str(embed_path))
        print("Embedder saved.")
    else:
        print("Embedder already exists at", embed_path)

    # Download/reranker model
    if not rerank_path.exists():
        print("Downloading reranker →", rerank_path)
        model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L6-v2")
        model.save(str(rerank_path))
        print("Reranker saved.")
    else:
        print("Reranker already exists at", rerank_path)

    print("Done. Local models are ready for offline use.")

if __name__ == "__main__":
    main()
