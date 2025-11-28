import argparse, json, re
from pathlib import Path
from src.rag_mcp.ingest.fetch_html import load_html
from src.rag_mcp.ingest.parse_sunway import extract_sections
from src.rag_mcp.ingest.normalize import build_programme_json
from src.rag_mcp.ingest.validate import validate_programme
from src.rag_mcp.config import JSON_DIR, HTML_DIR, BASE_DIR
import os

def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+","-", s.lower()).strip("-")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", help="path to saved HTML")
    ap.add_argument("--url", help="source URL (for metadata only)")
    ap.add_argument("--programme_name", required=True)
    ap.add_argument("--school", default="")
    ap.add_argument("--level", default="Undergraduate")
    ap.add_argument("--duration", default="")
    ap.add_argument("--intakes", nargs="*", default=[])
    args = ap.parse_args()

    html = load_html(args.html) if args.html else ""
    minimal = extract_sections(html)
    pid = f"sunway:{slugify(args.school or 'sc')}:{slugify(args.programme_name)}"
    meta = {
        "programme_name": args.programme_name,
        "school": args.school,
        "level": args.level,
        "duration": args.duration,
        "intakes": args.intakes
    }
    obj = build_programme_json(minimal, args.url or "https://sunwayuniversity.edu.my", pid, meta)
    out = Path(JSON_DIR) / f"{slugify(args.programme_name)}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    validate_programme(obj, str(Path(BASE_DIR) / "src/rag_mcp/schemas/programme.schema.json"))
    out.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
