from pathlib import Path

def load_html(path_or_str: str) -> str:
    p = Path(path_or_str)
    return p.read_text(encoding="utf-8")
