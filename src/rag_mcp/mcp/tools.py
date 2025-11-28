# src/rag_mcp/mcp/tools.py
from typing import Dict, List, Optional, Tuple
import re, json, math
from pathlib import Path

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer, util

from ..config import CHROMA_DIR, COLLECTION, TOP_K, JSON_DIR, EMBED_MODEL
from ..index.reranker import rerank as maybe_rerank

# -------- intent routing --------
FEE_WORDS = re.compile(r"\b(fee|fees|tuition|per\s*year|cost|price|annual)\b", re.I)
STRUCTURE_WORDS = re.compile(r"\b(year\s*\d|structure|modules?|subjects?)\b", re.I)
OVERVIEW_WORDS = re.compile(r"\b(overview|what\s+is|about|summary)\b", re.I)
YEAR_CAPTURE = re.compile(r"year\s*(\d)", re.I)

def _classify_section_year(q: str) -> Tuple[Optional[str], Optional[int]]:
    if FEE_WORDS.search(q): return ("fees", None)
    if STRUCTURE_WORDS.search(q):
        m = YEAR_CAPTURE.search(q)
        return ("structure", int(m.group(1)) if m else None)
    if OVERVIEW_WORDS.search(q): return ("overview", None)
    return (None, None)

# -------- load corpus programme names + embed once -------- changed into
# -------- load corpus programme names (lazy) + embed once --------
_JSON_DIR = Path(JSON_DIR)  # use absolute path from config

def _load_programme_names() -> List[str]:
    names = []
    if _JSON_DIR.exists():
        for p in _JSON_DIR.glob("*.json"):
            try:
                obj = json.loads(p.read_text(encoding="utf-8"))
                n = (obj.get("programme_name") or "").strip()
                if n:
                    names.append(n)
            except Exception:
                continue
    # dedupe case-insensitive, keep first occurrence
    seen = set()
    out: List[str] = []
    for n in names:
        k = n.lower()
        if k not in seen:
            seen.add(k)
            out.append(n)
    return out

PROGRAMME_NAMES: Optional[List[str]] = None
_MODEL: Optional[SentenceTransformer] = None
_PROG_EMB = None  # type: ignore

def _ensure_model_and_programmes() -> None:
    global PROGRAMME_NAMES, _MODEL, _PROG_EMB
    if PROGRAMME_NAMES is None:
        PROGRAMME_NAMES = _load_programme_names()
    if _MODEL is None:
        _MODEL = SentenceTransformer(EMBED_MODEL)
    if PROGRAMME_NAMES and _PROG_EMB is None:
        _PROG_EMB = _MODEL.encode(PROGRAMME_NAMES, normalize_embeddings=True)

def _pick_programme_name(query: str) -> Optional[str]:
    _ensure_model_and_programmes()
    if not PROGRAMME_NAMES or _PROG_EMB is None:
        return None

    q_emb = _MODEL.encode([query], normalize_embeddings=True)  # type: ignore[arg-type]
    sims = util.cos_sim(q_emb, _PROG_EMB)[0]  # shape: [N]
    top_idx = int(sims.argmax().item())
    top_sim = float(sims[top_idx])
    return PROGRAMME_NAMES[top_idx] if top_sim >= 0.35 else None  # conservative threshold

# -------- Chroma helpers --------
def _get_col():
    client = chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(allow_reset=False))
    return client.get_or_create_collection(name=COLLECTION, metadata={"hnsw:space": "cosine"})

def _where(section: Optional[str], year: Optional[int], programme: Optional[str]) -> Optional[Dict]:
    terms=[]
    if section:   terms.append({"section": {"$eq": section}})
    if year is not None: terms.append({"year": {"$eq": year}})
    if programme: terms.append({"programme_name": {"$eq": programme}})
    if not terms: return None
    return terms[0] if len(terms)==1 else {"$and": terms}

def _query(col, query: str, n_pre: int, where: Optional[Dict]):
    return col.query(query_texts=[query], n_results=n_pre,
                     include=["documents","metadatas","distances"], where=where)

def _query_with_backoff(col, query: str, n_pre: int,
                        section: Optional[str], year: Optional[int],
                        programme: Optional[str]):
    # A) programme + section/year
    res = _query(col, query, n_pre, _where(section, year, programme))
    if res.get("documents") and res["documents"][0]: return res
    # B) programme only (drop section/year first)
    if programme:
        res = _query(col, query, n_pre, _where(None, None, programme))
        if res.get("documents") and res["documents"][0]: return res
    # C) no filter
    return _query(col, query, n_pre, None)

# -------- public tools --------
def search(query: str, top_k: int = TOP_K) -> Dict:
    col = _get_col()
    section, year = _classify_section_year(query)
    programme = _pick_programme_name(query)

    n_pre = max(top_k, 20)
    res = _query_with_backoff(col, query, n_pre, section, year, programme)

    cands: List[Dict] = []
    n = len(res["documents"][0]) if res.get("documents") else 0
    for i in range(n):
        cands.append({
            "id": res["ids"][0][i],
            "text": res["documents"][0][i],
            "score": 1.0 - float(res["distances"][0][i]) if res.get("distances") else 0.0,
            "metadata": res["metadatas"][0][i] if res.get("metadatas") else {}
        })

    # tiny heuristic boost for exact programme match before rerank
    if programme:
        pl = programme.lower()
        for c in cands:
            if (c.get("metadata",{}) or {}).get("programme_name","").lower() == pl:
                c["score"] += 0.05

    cands = maybe_rerank(query, cands)
    return {"results": cands[:top_k]}

def get(doc_id: str) -> Dict:
    col = _get_col()
    out = col.get(ids=[doc_id], include=["documents","metadatas"])
    return {"id": out["ids"][0], "text": out["documents"][0], "metadata": out["metadatas"][0]}
