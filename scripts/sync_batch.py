# scripts/sync_batch.py (only the make_programme_json() differs slightly)
import argparse, json, hashlib, re
from pathlib import Path
from datetime import date
from src.rag_mcp.config import HTML_DIR, JSON_DIR, BASE_DIR
from src.rag_mcp.ingest.fetch_html import load_html
from src.rag_mcp.ingest.parse_sunway import extract_sections
from src.rag_mcp.ingest.validate import validate_programme

SCHEMA_PATH = Path(BASE_DIR) / "src/rag_mcp/schemas/programme.schema.json"

def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

def compute_content_hash(obj) -> str:
    data = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()

def make_programme_json(html_path: Path, defaults) -> dict:
    from src.rag_mcp.ingest.normalize import parse_fees  # reuse common logic

    html = load_html(str(html_path))
    mini = extract_sections(html)  # overview_text, structure[], fees_text, fees_note, duration, intakes, career_prospects

    # infer a temp programme_name from filename if not provided
    programme_name = defaults.programme_name or html_path.stem.replace("_", " ").replace("-", " ").title()
    pid = f"sunway:{slugify(defaults.school or 'sc')}:{slugify(programme_name)}"

    fees = parse_fees(mini.get("fees_text",""), mini.get("fees_note",""))
    duration = mini.get("duration") or (defaults.duration or "")
    intakes  = mini.get("intakes") or (defaults.intakes or "")
    intakes_list = [s.strip() for s in intakes.split(",") if s.strip()] if isinstance(intakes, str) else intakes

    payload = {
        "id": pid,
        "programme_name": programme_name,
        "school": defaults.school or "",
        "level": defaults.level or "Undergraduate",
        "duration": duration,
        "intakes": intakes_list,
        "url": defaults.url or "https://sunwayuniversity.edu.my",
        "overview_text": mini.get("overview_text","").strip(),
        "structure": mini.get("structure",[]),
        "fees": fees,
        "career_prospects": mini.get("career_prospects", []),
        "last_fetched": date.today().isoformat(),
    }

    payload["source_hash"] = compute_content_hash({
        "overview_text": payload["overview_text"],
        "structure": payload["structure"],
        "fees": payload["fees"],
        "duration": payload["duration"],
        "intakes": payload["intakes"],
        "career_prospects": payload["career_prospects"]
    })
    return payload

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default=str(Path(HTML_DIR) / "*.html"), help="Glob of HTML files")
    ap.add_argument("--url", default="")
    ap.add_argument("--programme_name", default="")
    ap.add_argument("--school", default="")
    ap.add_argument("--level", default="Undergraduate")
    ap.add_argument("--duration", default="")
    ap.add_argument("--intakes", default="")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    outdir = Path(JSON_DIR); outdir.mkdir(parents=True, exist_ok=True)
    changed, skipped = 0, 0

    for html_path in sorted(Path().glob(args.glob)):
        payload = make_programme_json(html_path, args)
        json_path = outdir / f"{slugify(payload['programme_name'])}.json"

        previous = None
        if json_path.exists():
            try:
                previous = json.loads(json_path.read_text(encoding="utf-8"))
            except Exception:
                previous = None

        if previous and (previous.get("source_hash") == payload["source_hash"]) and not args.force:
            skipped += 1
            continue

        validate_programme(payload, str(SCHEMA_PATH))
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        changed += 1
        print(f"[updated] {json_path.name}")

    print(f"\nDone. Updated: {changed}  Skipped (unchanged): {skipped}  JSON dir: {outdir}")

if __name__ == "__main__":
    main()
