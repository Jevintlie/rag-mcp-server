import json, jsonschema
from pathlib import Path

def validate_programme(obj: dict, schema_path: str):
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    jsonschema.validate(instance=obj, schema=schema)
