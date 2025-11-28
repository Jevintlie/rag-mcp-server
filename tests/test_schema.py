import json, glob
from pathlib import Path
from src.rag_mcp.ingest.validate import validate_programme
from src.rag_mcp.config import BASE_DIR, JSON_DIR

def test_programmes_validate():
    schema = str(Path(BASE_DIR) / "src/rag_mcp/schemas/programme.schema.json")
    files = glob.glob(str(Path(JSON_DIR) / "*.json"))
    for fp in files:
        obj = json.loads(Path(fp).read_text(encoding="utf-8"))
        validate_programme(obj, schema)
