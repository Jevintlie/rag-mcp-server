import json
from pathlib import Path

import pytest
from jsonschema import ValidationError

from rag_mcp.ingest.validate import validate_programme


ROOT = Path(__file__).parents[1]
SCHEMA = ROOT / "src" / "rag_mcp" / "schemas" / "programme.schema.json"
FIXTURE = Path(__file__).parent / "fixtures" / "sample_bsc_cs.json"


def test_sample_programme_matches_the_public_schema():
    validate_programme(json.loads(FIXTURE.read_text(encoding="utf-8")), str(SCHEMA))


def test_schema_rejects_missing_source_metadata():
    programme = json.loads(FIXTURE.read_text(encoding="utf-8"))
    del programme["source_hash"]
    with pytest.raises(ValidationError):
        validate_programme(programme, str(SCHEMA))
