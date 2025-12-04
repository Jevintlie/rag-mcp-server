# scripts/eval_smoke.py

from rag_mcp.mcp.tools import search


def main() -> None:
    tests = [
        "How much is BSc Computer Science per year?",
        "What are the Year 2 modules for Information Systems?",
        "Give me the overview of Business Management.",
    ]

    for q in tests:
        r = search(q, top_k=5)
        results = r.get("results") or []

        top = results[0] if results else {}
        meta = top.get("metadata") or {}

        section = meta.get("section")
        programme = meta.get("programme_name")

        print(q, "→", section, programme)


if __name__ == "__main__":
    main()
