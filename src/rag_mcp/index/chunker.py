# src/rag_mcp/index/chunker.py
from typing import Dict, List, Any

def _fees_line(p: Dict[str, Any]) -> str:
    fees = p.get("fees", {}) or {}
    parts = []
    if fees.get("malaysian_rm") is not None:
        try:
            parts.append(f"RM{int(fees['malaysian_rm'])} (Malaysian)")
        except Exception:
            pass
    if fees.get("international_usd") is not None:
        try:
            parts.append(f"USD{int(fees['international_usd'])} (International)")
        except Exception:
            pass

    if parts:
        line = " — Estimated Annual Course Fee: " + "; ".join(parts) + ". "
    else:
        line = " — Fees unavailable on source page. "

    if fees.get("notes"):
        line += f"Note: {fees['notes']}. "

    return line

def make_chunks(p: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Build retrieval-friendly chunks from a single programme JSON.

    Returns a list of dicts with:
      - id: stable unique id (programme_id + section)
      - text: chunk text
      - metadata: { programme_name, section, year?, url, last_fetched }
    """
    chunks: List[Dict[str, Any]] = []

    programme_name = p.get("programme_name", "").strip()
    url = p.get("url", "").strip()
    last_fetched = p.get("last_fetched", "").strip()

    # -------- Fees chunk (concise, precise, first-class) + synonym boost
    fee_line = _fees_line(p)
    fees_text = (
        f"Programme: {programme_name}{fee_line}"
        f"Source: {url}. "
        # ---- Retrieval synonym boost (one short line) ----
        f"(synonyms: tuition, per year, annual fee, yearly cost, programme cost, price)"
    )
    chunks.append({
        "id": f"{p['id']}#fees",
        "text": fees_text,
        "metadata": {
            "programme_name": programme_name,
            "section": "fees",
            "year": None,
            "url": url,
            "last_fetched": last_fetched
        }
    })

    # -------- Overview chunk
    overview = (p.get("overview_text") or "").strip()
    if overview:
        chunks.append({
            "id": f"{p['id']}#overview",
            "text": overview,
            "metadata": {
                "programme_name": programme_name,
                "section": "overview",
                "year": None,
                "url": url,
                "last_fetched": last_fetched
            }
        })

    # -------- Programme structure: one chunk per year
    for y in p.get("structure", []) or []:
        year = y.get("year")
        modules = [m.strip() for m in (y.get("modules") or []) if m and m.strip()]
        if not modules:
            continue
        txt = f"Year {year}: " + "; ".join(modules)
        chunks.append({
            "id": f"{p['id']}#y{year}",
            "text": txt,
            "metadata": {
                "programme_name": programme_name,
                "section": "structure",
                "year": year,
                "url": url,
                "last_fetched": last_fetched
            }
        })

    return chunks
