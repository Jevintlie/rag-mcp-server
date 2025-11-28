from src.rag_mcp.mcp.tools import search
tests = [
  "How much is BSc Computer Science per year?",
  "What are the Year 2 modules for Information Systems?",
  "Give me the overview of Business Management."
]
for q in tests:
    r = search(q, top_k=5)
    top = r["results"][0] if r["results"] else {}
    print(q, "→", (top.get("metadata") or {}).get("section"), (top.get("metadata") or {}).get("programme_name"))
