import json
from pathlib import Path

from rag_mcp.index.chunker import make_chunks


FIXTURE = Path(__file__).parent / "fixtures" / "sample_bsc_cs.json"


def test_chunker_creates_stable_retrieval_sections():
    programme = json.loads(FIXTURE.read_text(encoding="utf-8"))
    chunks = make_chunks(programme)

    assert [chunk["id"] for chunk in chunks] == [
        "sunway:set:computer-science-example#fees",
        "sunway:set:computer-science-example#overview",
        "sunway:set:computer-science-example#y1",
        "sunway:set:computer-science-example#y2",
    ]
    assert {chunk["metadata"]["section"] for chunk in chunks} == {
        "fees",
        "overview",
        "structure",
    }
    assert "Synthetic values" in chunks[0]["text"]
