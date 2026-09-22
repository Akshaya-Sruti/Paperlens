"""Metadata, title, author, year and keyword extraction.

Strategy: trust PDF metadata only when it looks sane, otherwise fall
back to conservative first-page heuristics. Anything uncertain is
returned as None / [] — never invented. This module is intentionally
LLM-free and will be enhanced (not replaced) by smarter extractors
in later stages.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import fitz

from app.models.paper import RawMetadata

_WS = re.compile(r"\s+")
_PDF_DATE = re.compile(
    r"D:(\d{4})(\d{2})?(\d{2})?(\d{2})?(\d{2})?(\d{2})?"
)
_YEAR = re.compile(r"\b((?:19|20)\d{2})\b")
_COPYRIGHT_YEAR = re.compile(r"(?:©|copyright|\(c\))\s*((?:19|20)\d{2})", re.I)
_ARXIV = re.compile(r"arXiv:(\d{2})(\d{2})\.\d+", re.I)

_AFFILIATION_HINTS = (
    "university",
    "institute",
    "department",
    "college",
    "school",
    "laboratory",
    "laboratories",
    "centre",
    "center",
    "academy",
    "faculty",
    "@",
    ".edu",
    "http",
    "correspondence",
    "address",
)

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
_ARXIV_LINE_RE = re.compile(r"arxiv", re.I)


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    text = _WS.sub(" ", str(value)).strip(" \t\n\r\x0b\x0c-–—:;,.|")
    return text or None


def parse_pdf_date(raw: str | None) -> tuple[str | None, int | None]:
    """Parse 'D:YYYYMMDDHHmmSSOHH'mm'' into (iso_date, year)."""
    if not raw:
        return None, None
    m = _PDF_DATE.search(raw.strip())
    if not m:
        return None, None
    year = int(m.group(1))
    if year < 1900 or year > 2100:
        return None, None
    parts = [m.group(1), m.group(2) or "01", m.group(3) or "01"]
    iso = f"{parts[0]}-{parts[1]}-{parts[2]}"
    return iso, year


def extract_raw_metadata(doc: fitz.Document) -> RawMetadata:
    meta = doc.metadata or {}
    creation, _ = parse_pdf_date(meta.get("creationDate"))
    modified, _ = parse_pdf_date(meta.get("modDate"))
    return RawMetadata(
        title_raw=_clean(meta.get("title")),
        author_raw=_clean(meta.get("author")),
        subject=_clean(meta.get("subject")),
        keywords=_clean(meta.get("keywords")),
        creator=_clean(meta.get("creator")),
        producer=_clean(meta.get("producer")),
        creation_date=creation,
        modification_date=modified,
    )


def _metadata_title_usable(title: str | None, filename: str) -> bool:
    if not title:
        return False
    if len(title) < 8 or len(title) > 300:
        return False
    if len(title.split()) < 2:
        return False
    stem = filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ")
    if title.lower() == stem.lower():
        return False
    # Export artefacts such as "Microsoft Word - paper.docx".
    if re.match(r"^(microsoft word|word|untitled|document\d*)\b", title, re.I):
        return False
    if _ARXIV_LINE_RE.search(title) and len(title.split()) < 3:
        return False
    return True


@dataclass
class _Line:
    text: str
    size: float
    y: float


def _first_page_lines(doc: fitz.Document) -> list[_Line]:
    """Text lines of page 1 in reading order with font size + position."""
    if doc.page_count == 0:
        return []
    page = doc[0]
    height = page.rect.height or 1.0
    lines: list[_Line] = []
    try:
        data = page.get_text("dict")
    except Exception:
        return []
    for block in data.get("blocks", []):
        if block.get("type", 0) != 0:
            continue
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            text = _WS.sub(" ", "".join(s.get("text", "") for s in spans)).strip()
            if not text:
                continue
            sizes = [s.get("size", 0) for s in spans if s.get("text", "").strip()]
            size = max(sizes) if sizes else 0
            y = line.get("bbox", [0, 0, 0, 0])[1] / height  # 0 top → 1 bottom
            lines.append(_Line(text=text, size=float(size), y=float(y)))
    lines.sort(key=lambda line: (round(line.y, 3)))
    return lines


def _looks_like_header_noise(text: str) -> bool:
    lowered = text.lower()
    if _EMAIL_RE.search(text):
        return True
    if _ARXIV_LINE_RE.search(text):
        return True
    if _AFFILIATION_RE.search(lowered):
        return True
    if re.match(r"^(vol\.|volume|pp\.|pages?|chapter|journal|conference|proceedings)\b", lowered):
        return True
    return False


_AFFILIATION_RE = re.compile(
    r"\b(universit\w*|institute\w*|department\w*|college\w*|school\w*|"
    r"laborator\w*|centre\w*|center\w*|academ\w*|facult\w*|polytechnic\w*|"
    r"research|lab|labs|brain|inc\.?|corp\.?|ltd\.?|gmbh)\b"
)


def detect_title(
    doc: fitz.Document, raw: RawMetadata, filename: str
) -> str | None:
    if _metadata_title_usable(raw.title_raw, filename):
        return raw.title_raw

    lines = [ln for ln in _first_page_lines(doc) if ln.y < 0.45]
    if not lines:
        return None
    content = [ln for ln in lines if not _looks_like_header_noise(ln.text)]
    if not content:
        return None

    top_size = max(ln.size for ln in content)
    if top_size <= 0:
        return None
    # Title lines: large type near the top. Preamble matter (copyright
    # notices, permission text) is skipped until the first large line.
    picked: list[str] = []
    started = False
    for ln in content[:12]:
        if not started:
            if ln.size < top_size - 1.5:
                continue
            started = True
        elif ln.size < top_size - 1.5:
            break
        if len(ln.text) < 3:
            continue
        picked.append(ln.text)
        if len(picked) >= 3:
            break
    title = _clean(" ".join(picked))
    if not title or len(title) < 10 or len(title.split()) < 3:
        return None
    if len(title) > 300:
        return None
    return title


def detect_year(doc: fitz.Document, raw: RawMetadata) -> int | None:
    # Explicit in-text evidence first: PDF file dates usually describe
    # the file (download/export), not the publication.
    try:
        first_text = doc[0].get_text("text") or ""
    except Exception:
        first_text = ""
    head = first_text[:4000]
    m = _COPYRIGHT_YEAR.search(head)
    if m:
        return int(m.group(1))
    m = _ARXIV.search(head)
    if m:
        yy = int(m.group(1))
        return 2000 + yy if yy <= 30 else 1900 + yy
    for value in (raw.creation_date, raw.modification_date):
        if value:
            m = _YEAR.search(value)
            if m:
                year = int(m.group(1))
                if 1900 <= year <= 2100:
                    return year
    return None
