from bs4 import BeautifulSoup, NavigableString, Tag
from typing import Dict, List, Optional
import re

RM_RE  = re.compile(r"RM\s*([0-9][0-9.,]*)", re.I)
USD_RE = re.compile(r"USD\s*([0-9][0-9.,]*)", re.I)

OVERVIEW_TITLES = [
    "Overview",
    "Programme Overview",
    "Program Overview",
    "About the Programme",
    "About the Program",
    "About the Course",
]

def _clean_text(s: Optional[str]) -> str:
    if not s: return ""
    return " ".join(s.split())

def _collect_until_next_section(start: Tag, max_chars: int = 4000) -> str:
    """
    Starting from the node after `start`, collect text from <p>, <ul>/<ol><li>, and plain strings
    until we hit the next H2/H3 (a new section) or we exceed max_chars.
    """
    parts: List[str] = []
    node = start.next_sibling
    collected = 0
    while node and collected < max_chars:
        if isinstance(node, NavigableString):
            txt = _clean_text(str(node))
            if txt:
                parts.append(txt)
                collected += len(txt)
        elif isinstance(node, Tag):
            # Stop at the next high-level section heading
            if node.name in ("h2", "h3"):
                break
            # Paragraphs
            if node.name == "p":
                txt = _clean_text(node.get_text(" "))
                if txt:
                    parts.append(txt)
                    collected += len(txt)
            # Bullet lists (sometimes used for overview bullets)
            if node.name in ("ul", "ol"):
                items = []
                for li in node.find_all("li", recursive=False):
                    t = _clean_text(li.get_text(" "))
                    if t: items.append(f"• {t}")
                if items:
                    block = " ".join(items)
                    parts.append(block)
                    collected += len(block)
        node = node.next_sibling

    # Fallback: if nothing captured (sometimes content is wrapped), try the next siblings’ descendants
    text = " ".join(parts).strip()
    if not text:
        nxt = start.find_next(["p","ul","ol"])
        while nxt and collected < max_chars:
            if nxt.name == "p":
                t = _clean_text(nxt.get_text(" "))
                if t:
                    parts.append(t); collected += len(t)
            elif nxt.name in ("ul","ol"):
                items = []
                for li in nxt.find_all("li", recursive=False):
                    t = _clean_text(li.get_text(" "))
                    if t: items.append(f"• {t}")
                if items:
                    block = " ".join(items)
                    parts.append(block); collected += len(block)
            nxt = nxt.find_next_sibling()
            # stop at next section heading
            if nxt and nxt.name in ("h2","h3"):
                break
        text = " ".join(parts).strip()
    return text

def _find_overview(soup: BeautifulSoup) -> str:
    # 1) Direct anchor/id patterns
    #   <section id="overview"> ... </section>  OR  <div id="programme-overview"> ...</div>
    for sel in ['#overview', '[id*="overview" i]', 'a[name="overview" i]']:
        node = soup.select_one(sel)
        if node:
            # If this is a section/div with content, pull paragraphs inside
            if isinstance(node, Tag) and node.name not in ("a",):
                txt = _clean_text(node.get_text(" "))
                if txt:
                    return txt[:4000]
            # If it's an anchor <a name="overview">, collect after the nearest heading
            if node.name == "a":
                h = node.find_next(["h2","h3","p"])
                if h and h.name in ("h2","h3"):
                    return _collect_until_next_section(h)
                elif h and h.name == "p":
                    # gather a few paragraphs
                    txts = []
                    cur = h
                    total = 0
                    while cur and total < 4000 and cur.name == "p":
                        t = _clean_text(cur.get_text(" "))
                        if t:
                            txts.append(t); total += len(t)
                        cur = cur.find_next_sibling()
                    if txts:
                        return " ".join(txts)

    # 2) Heading text variants: find <h2>/<h3> whose text matches any OVERVIEW_TITLES
    for h in soup.find_all(["h2","h3"]):
        title = _clean_text(h.get_text(" ")).lower()
        if any(title == t.lower() for t in OVERVIEW_TITLES):
            txt = _collect_until_next_section(h)
            if txt:
                return txt

    # 3) Body field fallbacks (Drupal-style fields)
    for sel in [
        "div.field--name-body",
        "article .field--name-body",
        ".node__content .field--name-body",
        ".region-content .node__content",
    ]:
        n = soup.select_one(sel)
        if n:
            txt = _clean_text(n.get_text(" "))
            if txt:
                return txt[:4000]

    # 4) Very last resort: first 2–4 paragraphs in the main article
    art = soup.select_one("article") or soup.select_one("main") or soup.select_one(".region-content")
    if art:
        ps = art.find_all("p", limit=4)
        txts = [_clean_text(p.get_text(" ")) for p in ps if _clean_text(p.get_text(" "))]
        if txts:
            return " ".join(txts)[:4000]

    return ""  # give up

def extract_sections(html: str) -> Dict:
    """
    Returns:
      {
        overview_text: str,
        structure: [{year:int, modules:[str,..]}, ...],
        fees_text: str,            # raw (kept for debugging)
        fees_note: str,            # extra USD note when present
        duration: str,
        intakes: str,              # comma-separated (raw)
        career_prospects: [str,..] # optional
      }
    """
    soup = BeautifulSoup(html, "html.parser")

    # -------- Overview (robust)
    overview_text = _find_overview(soup)

    # -------- Programme Structure (split by Year headings + <ul>)
    structure = []
    for year in range(1, 7):
        hx = soup.find(lambda tag: tag.name in ["h2","h3","h4"] and f"Year {year}" in tag.get_text())
        if not hx:
            continue
        ul = hx.find_next("ul")
        modules = []
        if ul:
            for li in ul.find_all("li", recursive=False):
                t = _clean_text(li.get_text(" "))
                if t:
                    modules.append(t)
        if modules:
            structure.append({"year": year, "modules": modules})

    # -------- Duration / Intakes (stable classes seen on Sunway pages)
    duration_node = soup.select_one(".coursedurationbox .coursedurationfield")
    intakes_node  = soup.select_one(".views-field-field-intakes .field-content")
    duration = _clean_text(duration_node.get_text(" ")) if duration_node else ""
    intakes  = _clean_text(intakes_node.get_text(" "))  if intakes_node  else ""

    # -------- Career Prospects (optional)
    career_nodes = soup.select(".views-field-field-career-prospects ul li")
    career_prospects = [_clean_text(li.get_text(" ")) for li in career_nodes if _clean_text(li.get_text(" "))]

    # -------- Fees block (label is often 'Estimated Annual Course Fee')
    fees_container = soup.select_one(".views-field-field-malaysian-student-fees")
    fees_text, fees_note = "", ""
    if fees_container:
        fees_text = _clean_text(fees_container.get_text(" "))
        m = re.search(r"([^.]*?(?:indicative|exchange rate)[^.]*\.)", fees_text, re.I)
        if m:
            fees_note = _clean_text(m.group(1))

    return {
        "overview_text": overview_text,
        "structure": structure,
        "fees_text": fees_text,
        "fees_note": fees_note,
        "duration": duration,
        "intakes": intakes,
        "career_prospects": career_prospects
    }
