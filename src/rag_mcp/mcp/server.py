# src/rag_mcp/mcp/server.py
import sys, json, argparse, logging, time, traceback, os
from typing import Any, Dict, Optional
from ..mcp.tools import search as rag_search, get as rag_get

# ---------- JSON logging ----------
class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(record.created)),
            "level": record.levelname,
            "name": record.name,
            "msg": record.getMessage(),
        }
        for k, v in getattr(record, "__dict__", {}).items():
            if k not in ("ts","level","name","msg"):
                try:
                    json.dumps(v); payload[k]=v
                except Exception:
                    payload[k]=str(v)
        return json.dumps(payload, ensure_ascii=False)

def configure_logging(log_json: bool, level: str) -> None:
    lvl = getattr(logging, level.upper(), logging.INFO)
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(lvl)
    h = logging.StreamHandler(sys.stderr)
    h.setLevel(lvl)
    h.setFormatter(JsonFormatter() if log_json else logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    root.addHandler(h)

log = logging.getLogger("rag_mcp.server")

# ---------- JSON-RPC helpers ----------
def _write(obj: Dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()

def _error(id_: Optional[Any], code: int, message: str, data: Optional[Dict[str, Any]] = None) -> None:
    resp = {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}
    if data is not None:
        resp["error"]["data"] = data
    _write(resp)

def _result(id_: Any, result: Any) -> None:
    _write({"jsonrpc": "2.0", "id": id_, "result": result})

# ---------- MCP tool definitions ----------
def _list_tools_obj() -> Dict[str, Any]:
    return {
        "tools": [
            {
                "name": "rag.search",
                "description": "Semantic search over Sunway programmes with filters and reranking.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "top_k": {"type": "integer", "minimum": 1, "maximum": 50}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "rag.get",
                "description": "Fetch a stored chunk by id (text + metadata).",
                "inputSchema": {
                    "type": "object",
                    "properties": {"id": {"type": "string"}},
                    "required": ["id"]
                }
            }
        ]
    }

def _call_tool(name: str, params: Dict[str, Any]) -> Any:
    if name == "rag.search":
        q = params.get("query", "")
        k = int(params.get("top_k", 5))
        log.debug("rag.search: request", extra={"query": q, "top_k": k})
        out = rag_search(q, top_k=k)
        preview = [{"id": r.get("id"),
                    "section": (r.get("metadata") or {}).get("section"),
                    "programme": (r.get("metadata") or {}).get("programme_name")}
                   for r in out.get("results", [])[:5]]
        log.info("rag.search: response", extra={"query": q, "top_k": k, "preview": preview})
        return out
    if name == "rag.get":
        doc_id = params.get("id", "")
        log.debug("rag.get: request", extra={"id": doc_id})
        out = rag_get(doc_id)
        log.info("rag.get: response", extra={"id": doc_id, "section": (out.get("metadata") or {}).get("section")})
        return out
    raise ValueError(f"Unknown tool: {name}")

# ---------- MCP protocol: minimal handlers ----------
PROTOCOL_VERSION = "2024-11-05"  # acceptable recent MCP protocol tag
SERVER_NAME = "sunway-rag"

def _handle_initialize(_params: Dict[str, Any]) -> Dict[str, Any]:
    # Minimal MCP initialize response:
    # - protocolVersion (string)
    # - serverInfo: { name, version }
    # - capabilities: declare what we support
    return {
        "protocolVersion": PROTOCOL_VERSION,
        "serverInfo": {"name": SERVER_NAME, "version": "1.0.0"},
        "capabilities": {
            "tools": {},            # we implement tools/list + tools/call
            "prompts": {},          # not implemented but harmless to expose as empty
            "resources": {},        # not implemented
            "logging": {"level": "info"}  # optional
        }
    }

def _handle_tools_list() -> Dict[str, Any]:
    return _list_tools_obj()

def _handle_tools_call(params: Dict[str, Any]) -> Dict[str, Any]:
    name = params.get("name")
    arguments = params.get("arguments") or {}
    res = _call_tool(name, arguments)

    # MCP CallToolResult JSON shape:
    # - content: list[ContentBlock]
    # - structuredContent: optional structured JSON (camelCase in JSON)
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(res, ensure_ascii=False),
            }
        ],
        # This is optional but very nice for clients that use structured data
        "structuredContent": res,
    }

def _handle_ping(_params: Dict[str, Any]) -> Dict[str, Any]:
    return {"ok": True, "ts": time.time()}

# ---------- main stdio loop ----------
def serve_stdio() -> None:
    log.info("MCP stdio server started", extra={"transport":"stdio","tools":["rag.search","rag.get"]})
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            _error(None, -32700, "Parse error")
            continue

        if not isinstance(req, dict) or req.get("jsonrpc") != "2.0":
            _error(req.get("id") if isinstance(req, dict) else None, -32600, "Invalid Request")
            continue

        id_ = req.get("id")
        method = req.get("method")
        params = req.get("params") or {}

        try:
            if method == "initialize":
                _result(id_, _handle_initialize(params))
            elif method in ("tools/list", "tools.list"):
                _result(id_, _handle_tools_list())
            elif method in ("tools/call", "tools.call"):
                _result(id_, _handle_tools_call(params))
            elif method == "ping":
                _result(id_, _handle_ping(params))
            else:
                _error(id_, -32601, f"Method not found: {method}")
        except Exception as e:
            log.error("Unhandled server error", extra={"exc": traceback.format_exc()})
            _error(id_, -32603, "Internal error", {"detail": str(e)})

# ---------- CLI ----------
def main() -> None:
    p = argparse.ArgumentParser(description="RAG MCP server")
    p.add_argument("--stdio", action="store_true", default=True, help="Use stdio transport (default)")
    p.add_argument("--no-stdio", dest="stdio", action="store_false", help="Disable stdio")
    p.add_argument("--log-json", action="store_true", help="Emit JSON logs to stderr")
    p.add_argument("--log-level", default="INFO", choices=["DEBUG","INFO","WARNING","ERROR"], help="Logging level")
    args = p.parse_args()

    configure_logging(args.log_json, args.log_level)

    if sys.platform.startswith("win"):
    # Python 3.7+ only
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    # Optional: disable Chroma telemetry noise
    os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

    if args.stdio:
        serve_stdio()
    else:
        log.error("Only stdio is implemented. Use --stdio.")
        sys.exit(2)

if __name__ == "__main__":
    main()
