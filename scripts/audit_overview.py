# scripts/audit_overview.py
import json, os, glob
from pathlib import Path

json_dir = Path("data/json")
missing=[]
for fp in glob.glob(str(json_dir/"*.json")):
    obj = json.loads(open(fp, encoding="utf-8").read())
    has_overview = bool(obj.get("overview_text","").strip())
    if not has_overview:
        missing.append(obj.get("programme_name","<unknown>"))
print(f"Programmes missing overview_text: {len(missing)}")
for m in missing[:50]:
    print(" -", m)
