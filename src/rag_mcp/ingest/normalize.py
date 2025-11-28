import re, json, hashlib
from datetime import date
from typing import Dict, Optional

FEE_RM  = re.compile(r"RM\s*([0-9][0-9.,]*)", re.I)
FEE_USD = re.compile(r"USD\s*([0-9][0-9.,]*)", re.I)

def _num_or_none(text: str, pat: re.Pattern) -> Optional[int]:
    m = pat.search(text or "")
    if not m: 
        return None
    raw = m.group(1).replace(",", "").replace(".", "")
    try:
        return int(raw)
    except Exception:
        return None

def parse_fees(fees_text: str, fees_note: str = "") -> Dict:
    rm  = _num_or_none(fees_text, FEE_RM)
    usd = _num_or_none(fees_text, FEE_USD)
    note = fees_note or ("International students pay RM equivalent; USD is indicative based on exchange rate." if usd else "")
    return {
        "malaysian_rm": rm,
        "international_usd": usd,
        "notes": note
    }

def compute_hash(obj: Dict) -> str:
    data = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()

def build_programme_json(minimal: Dict, url: str, programme_id: str, meta: Dict) -> Dict:
    fees = parse_fees(minimal.get("fees_text",""), minimal.get("fees_note",""))
    # prefer parsed duration/intakes if provided; fallback to meta defaults
    duration = minimal.get("duration") or meta.get("duration","")
    intakes  = []
    if minimal.get("intakes"):
        # normalize to list (split by comma)
        intakes = [s.strip() for s in minimal["intakes"].split(",") if s.strip()]
    elif meta.get("intakes"):
        intakes = meta["intakes"]

    payload = {
        "id": programme_id,
        "programme_name": meta.get("programme_name",""),
        "school": meta.get("school",""),
        "level": meta.get("level","Undergraduate"),
        "duration": duration,
        "intakes": intakes,
        "url": url,
        "overview_text": minimal.get("overview_text",""),
        "structure": minimal.get("structure",[]),
        "fees": fees,
        # include optional career prospects if present
        "career_prospects": minimal.get("career_prospects", []),
        "last_fetched": date.today().isoformat()
    }
    payload["source_hash"] = compute_hash({
        "overview_text": payload["overview_text"],
        "structure": payload["structure"],
        "fees": payload["fees"],
        "duration": payload["duration"],
        "intakes": payload["intakes"],
        "career_prospects": payload.get("career_prospects", [])
    })
    return payload
