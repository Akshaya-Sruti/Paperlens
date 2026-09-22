"""Section-aware AI input preparation (Stage 5).

Builds a deterministic, budgeted text representation from the stored
structured paper — never an uncontrolled dump. Priority order follows
academic importance; truncation (when needed) drops lower-priority
sections first and says so in the returned stats. Easy to replace
with RAG in a later stage: same inputs, same output contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Approximate input budget (~15k tokens at ~4 chars/token).
MAX_INPUT_CHARS = 60000
# Per-section ceiling so one giant section cannot crowd out the rest.
PER_SECTION_CHARS = 12000
# Reference appendix ceiling.
REFERENCES_CHARS = 3000

# Priority: earlier = more important. Matches academic reading order.
SECTION_PRIORITY = [
    "introduction",
    "methodology",
    "dataset",
    "experiments",
    "results",
    "discussion",
    "limitations",
    "conclusion",
    "future_work",
    "related_work",
    "background",
    "acknowledgements",
    "other",
]


@dataclass
class PreparedContext:
    text: str
    approx_input_chars: int = 0
    truncated: bool = False
    sections_included: list[str] = field(default_factory=list)


def _priority_key(section: dict) -> tuple[int, int]:
    try:
        order = SECTION_PRIORITY.index(section.get("normalized_type", "other"))
    except ValueError:
        order = len(SECTION_PRIORITY)
    return (order, section.get("start_page", 0))


def prepare_paper_context(stored: dict) -> PreparedContext:
    parts: list[str] = []
    used = 0
    included: list[str] = []
    truncated = False

    def push(block: str) -> bool:
        nonlocal used, truncated
        if used + len(block) > MAX_INPUT_CHARS:
            truncated = True
            return False
        parts.append(block)
        used += len(block)
        return True

    title = stored.get("title") or stored.get("filename", "Untitled")
    authors = stored.get("authors", [])
    names = ", ".join(
        a.get("name", "") if isinstance(a, dict) else str(a) for a in authors
    )
    header = [
        f"TITLE:\n{title}",
        f"AUTHORS:\n{names or 'Not detected'}",
        f"ABSTRACT:\n{stored.get('abstract') or 'Not detected'}",
    ]
    keywords = stored.get("keywords", [])
    if keywords:
        header.append("KEYWORDS:\n" + ", ".join(keywords))
    publication = stored.get("publication", {}) or {}
    venue_bits = [publication.get("venue"), stored.get("year")]
    venue_line = " · ".join(str(b) for b in venue_bits if b)
    if venue_line:
        header.append(f"VENUE:\n{venue_line}")
    for block in header:
        push(block + "\n")

    sections = sorted(stored.get("sections", []), key=_priority_key)
    for section in sections:
        title_s = section.get("title", "Untitled section")
        start, end = section.get("start_page", "?"), section.get("end_page", "?")
        content = (section.get("content") or "").strip()
        if len(content) > PER_SECTION_CHARS:
            content = content[:PER_SECTION_CHARS] + "\n[Section truncated for length.]"
            truncated = True
        block = (
            f"SECTION:\n{title_s}\nPAGE:\n{start}-{end}\nTEXT:\n{content}"
            if content
            else f"SECTION:\n{title_s}\nPAGE:\n{start}-{end}\nTEXT:\n[No extractable text.]"
        )
        if not push(block + "\n"):
            break
        included.append(title_s)

    figures = stored.get("figures", [])
    tables = stored.get("tables", [])
    if figures or tables:
        lines = []
        for fig in figures[:30]:
            caption = (fig.get("caption") or "").strip()
            lines.append(
                f"Figure {fig.get('number') or '?'} (page {fig.get('page', '?')}): {caption}"
            )
        for table in tables[:30]:
            caption = (table.get("caption") or "").strip()
            lines.append(
                f"Table {table.get('number') or '?'} (page {table.get('page', '?')}): {caption}"
            )
        push("FIGURES AND TABLES:\n" + "\n".join(lines) + "\n")

    references = stored.get("references", [])
    if references:
        ref_lines = []
        total = 0
        for ref in references:
            raw = (ref.get("raw_text") or "").strip()
            idx = ref.get("index")
            line = f"[{idx}] {raw}" if idx is not None else raw
            if total + len(line) > REFERENCES_CHARS:
                truncated = True
                break
            ref_lines.append(line)
            total += len(line)
        if ref_lines:
            push(
                f"REFERENCES ({len(references)} total, showing {len(ref_lines)}):\n"
                + "\n".join(ref_lines)
                + "\n"
            )

    text = "\n".join(parts)
    return PreparedContext(
        text=text,
        approx_input_chars=len(text),
        truncated=truncated,
        sections_included=included,
    )
