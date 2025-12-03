import os
from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
JSON_DIR = os.path.join(DATA_DIR, "json")
HTML_DIR = os.path.join(DATA_DIR, "html")
CHROMA_DIR = os.getenv("CHROMA_DIR", os.path.join(DATA_DIR, "chroma"))

# NEW: local models dir
MODELS_DIR = os.path.join(BASE_DIR, "models")

# Models – default to local folders, but still overridable by env
EMBED_MODEL = os.getenv(
    "EMBED_MODEL",
    os.path.join(MODELS_DIR, "all-MiniLM-L6-v2"),
)
RERANK_MODEL = os.getenv(
    "RERANK_MODEL",
    os.path.join(MODELS_DIR, "ms-marco-MiniLM-L6-v2"),
)

# Chunking
CHUNK_TOKENS = int(os.getenv("CHUNK_TOKENS", "600"))   # ~450 words
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "80"))  # ~60 words

# Retrieval
TOP_K = int(os.getenv("TOP_K", "5"))
COLLECTION = os.getenv("COLLECTION", "sunway_programmes")
