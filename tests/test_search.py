import pytest

from rag_mcp.mcp.server import _handle_initialize, _handle_tools_list
from rag_mcp.mcp.tools import _classify_section_year, _where, search


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("How much are the annual fees?", ("fees", None)),
        ("Show the Year 2 modules", ("structure", 2)),
        ("Give me an overview", ("overview", None)),
        ("What careers are available?", (None, None)),
    ],
)
def test_query_intent_routing(query, expected):
    assert _classify_section_year(query) == expected


def test_chroma_filter_combines_available_fields():
    assert _where("structure", 2, "Computer Science") == {
        "$and": [
            {"section": {"$eq": "structure"}},
            {"year": {"$eq": 2}},
            {"programme_name": {"$eq": "Computer Science"}},
        ]
    }


def test_server_advertises_only_implemented_capabilities():
    initialized = _handle_initialize({})
    assert initialized["capabilities"] == {"tools": {}}
    assert {tool["name"] for tool in _handle_tools_list()["tools"]} == {
        "rag.search",
        "rag.get",
    }


def test_search_rejects_invalid_requests_before_loading_models():
    with pytest.raises(ValueError, match="must not be empty"):
        search("   ")
    with pytest.raises(ValueError, match="between 1 and 50"):
        search("computer science", top_k=100)
