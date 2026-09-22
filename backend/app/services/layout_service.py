"""Layout-aware analysis: blocks, reading order, headers/footers.

Uses PyMuPDF's text dict (spans with font size/flags/bbox) to:
  1. build ordered text blocks per page,
  2. restore correct reading order on multi-column pages via row grouping,
  3. detect repeated header/footer lines across pages (removed conservatively),
  4. report whether the document uses a multi-column layout.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import fitz

from app.models.paper import Block
from app.services.text_clean import clean_text, normalize_line

# Bold flag in PyMuPDF span flags.
_BOLD_FLAG = 16

# Bands (fraction of page height) considered for header/footer detection.
_HEADER_BAND = 0.09
_FOOTER_BAND = 0.92


@dataclass
class DocLine:
    text: str
    x0: float
    x1: float
    y0: float
    y1: float
    size: float
    bold: bool
    gap_before: float = 0.0  # vertical gap to previous line's bottom
    spans: list[tuple[float, float, str]] = field(default_factory=list)  # (x0, x1, text)


@dataclass
class PageLayout:
    page_number: int
    width: float
    height: float
    lines: list[DocLine] = field(default_factory=list)  # reading order
    blocks: list[Block] = field(default_factory=list)  # reading order
    header_texts: set[str] = field(default_factory=set)
    footer_texts: set[str] = field(default_factory=set)


def extract_lines(page: fitz.Page) -> list[DocLine]:
    """Raw text lines of a page with typographic features, unsorted."""
    out: list[DocLine] = []
    try:
        data = page.get_text("dict")
    except Exception:
        return out
    prev_bottom: float | None = None
    for block in data.get("blocks", []):
        if block.get("type", 0) != 0:
            continue
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            text = re.sub(r"\s+", " ", "".join(s.get("text", "") for s in spans)).strip()
            if not text:
                continue
            x0, y0, x1, y1 = line.get("bbox", [0, 0, 0, 0])
            sizes = [s.get("size", 0) for s in spans if s.get("text", "").strip()]
            flags = [s.get("flags", 0) for s in spans]
            gap = 0.0 if prev_bottom is None else max(0.0, y0 - prev_bottom)
            span_cells = [
                (float(s["bbox"][0]), float(s["bbox"][2]), s.get("text", ""))
                for s in spans
                if s.get("text")
            ]
            out.append(
                DocLine(
                    text=text,
                    x0=float(x0),
                    x1=float(x1),
                    y0=float(y0),
                    y1=float(y1),
                    size=float(max(sizes) if sizes else 0),
                    bold=any(f & _BOLD_FLAG for f in flags),
                    gap_before=float(gap),
                    spans=span_cells,
                )
            )
            prev_bottom = float(y1)
    return out


def order_lines(lines: list[DocLine]) -> list[DocLine]:
    """Restore reading order via row grouping.

    Lines overlapping vertically form a row; rows go top→bottom and
    cells within a row go left→right. This handles single-column,
    two-column and mixed (full-width headings) layouts uniformly.
    """
    if not lines:
        return []
    by_y = sorted(lines, key=lambda ln: (ln.y0, ln.x0))
    rows: list[list[DocLine]] = []
    row_refs: list[float] = []  # y0 of the row's first line
    for ln in by_y:
        placed = False
        for idx, row in enumerate(rows):
            top = min(r.y0 for r in row)
            bottom = max(r.y1 for r in row)
            # Overlaps the row band (with small tolerance for sub/superscripts)
            # AND starts at essentially the same height. The second condition
            # stops chained overlaps from fusing a whole front-matter block
            # (multi-column author lines at staggered heights) into one row.
            if (
                ln.y0 <= bottom + 2
                and ln.y1 >= top - 2
                and abs(ln.y0 - row_refs[idx]) <= 3.0
            ):
                row.append(ln)
                placed = True
                break
        if not placed:
            rows.append([ln])
            row_refs.append(ln.y0)
    rows.sort(key=lambda row: min(r.y0 for r in row))
    ordered: list[DocLine] = []
    for row in rows:
        row.sort(key=lambda ln: ln.x0)
        ordered.extend(row)
    return ordered


def detect_column_count(layouts: list[PageLayout]) -> int:
    """1 or 2, via gutter analysis and line-start distribution.

    Two complementary signals: (a) pages where a vertical gutter band
    splits text into side-by-side cells, (b) pages whose line starts
    cluster in two distinct x zones (column-aware extractors that
    pre-split lines). Either signal on enough pages means two columns.
    """
    gutter_pages = 0
    bimodal_pages = 0
    checked = 0
    for layout in layouts:
        if layout.page_number == 1 or not layout.lines:
            continue
        checked += 1
        width = layout.width or 1.0
        gutter = find_gutter(layout.lines, width)
        if gutter is not None:
            gutter_pages += 1
        if _starts_bimodal(layout.lines, width):
            bimodal_pages += 1
    if not checked:
        return 1
    if gutter_pages / checked >= 0.3 or bimodal_pages / checked >= 0.4:
        return 2
    return 1


def find_gutter(lines: list[DocLine], page_width: float) -> float | None:
    """x-center of the widest empty vertical band in the middle of the page."""
    edges: list[float] = []
    for ln in lines:
        if len(ln.text) < 10:
            continue
        edges.append(ln.x0)
        edges.append(ln.x1)
    if len(edges) < 8:
        return None
    lo, hi = page_width * 0.30, page_width * 0.70
    marks = sorted(e for e in edges if lo <= e <= hi)
    if len(marks) < 4:
        return None
    best: tuple[float, float] | None = None  # (gap_width, center)
    for left, right in zip(marks, marks[1:]):
        gap = right - left
        if best is None or gap > best[0]:
            best = (gap, (left + right) / 2)
    if best and best[0] >= page_width * 0.025:
        return best[1]
    return None


def _starts_bimodal(lines: list[DocLine], page_width: float) -> bool:
    starts = [ln.x0 for ln in lines if len(ln.text) >= 20]
    if len(starts) < 10:
        return False
    left = sum(1 for x in starts if x < page_width * 0.40)
    right = sum(1 for x in starts if x > page_width * 0.52)
    return left >= len(starts) * 0.2 and right >= len(starts) * 0.2


def split_at_gutter(lines: list[DocLine], page_width: float) -> list[DocLine]:
    """Split lines crossing the column gutter into per-column cells.

    Some PDFs merge both columns into one dict line (x0 in the left
    column, x1 in the right). Without splitting, text from the two
    columns interleaves mid-sentence.
    """
    gutter = find_gutter(lines, page_width)
    if gutter is None:
        return lines
    out: list[DocLine] = []
    for ln in lines:
        if not (ln.x0 < gutter < ln.x1 and ln.x1 - ln.x0 > page_width * 0.5):
            out.append(ln)
            continue
        left_spans = [(x0, x1, t) for x0, x1, t in ln.spans if (x0 + x1) / 2 < gutter]
        right_spans = [(x0, x1, t) for x0, x1, t in ln.spans if (x0 + x1) / 2 >= gutter]
        if not left_spans or not right_spans:
            out.append(ln)
            continue
        for group in (left_spans, right_spans):
            text = re.sub(r"\s+", " ", "".join(t for _, _, t in group)).strip()
            if not text:
                continue
            out.append(
                DocLine(
                    text=text,
                    x0=min(x0 for x0, _, _ in group),
                    x1=max(x1 for _, x1, _ in group),
                    y0=ln.y0,
                    y1=ln.y1,
                    size=ln.size,
                    bold=ln.bold,
                    gap_before=ln.gap_before,
                    spans=group,
                )
            )
    return out


def detect_headers_footers(layouts: list[PageLayout]) -> tuple[set[str], set[str]]:
    """Lines repeated in the top/bottom bands across many pages.

    Conservative: exact normalized match, short text, present on at
    least 3 pages and 40% of pages.
    """
    tops: dict[str, int] = {}
    bottoms: dict[str, int] = {}
    n = len(layouts)
    for layout in layouts:
        height = layout.height or 1.0
        seen_top, seen_bottom = set(), set()
        for ln in layout.lines:
            norm = normalize_line(ln.text)
            if not norm or len(norm) > 140:
                continue
            if ln.y0 < height * _HEADER_BAND:
                seen_top.add(norm)
            elif ln.y0 > height * _FOOTER_BAND:
                seen_bottom.add(norm)
        for t in seen_top:
            tops[t] = tops.get(t, 0) + 1
        for t in seen_bottom:
            bottoms[t] = bottoms.get(t, 0) + 1
    threshold = max(3, int(n * 0.4))
    headers = {t for t, c in tops.items() if c >= threshold and n >= 3}
    footers = {t for t, c in bottoms.items() if c >= threshold and n >= 3}
    return headers, footers


def analyze_document(doc: fitz.Document) -> tuple[list[PageLayout], int]:
    """Full layout pass. Returns (page layouts, column count)."""
    layouts: list[PageLayout] = []
    for i in range(doc.page_count):
        page = doc[i]
        rect = page.rect
        raw_lines = extract_lines(page)
        split = split_at_gutter(raw_lines, float(rect.width) or 1.0)
        lines = order_lines(split)
        layouts.append(
            PageLayout(
                page_number=i + 1,
                width=float(rect.width),
                height=float(rect.height),
                lines=lines,
            )
        )
    headers, footers = detect_headers_footers(layouts)
    for layout in layouts:
        layout.header_texts = headers
        layout.footer_texts = footers
    columns = detect_column_count(layouts)
    return layouts, columns


def page_text_clean(layout: PageLayout) -> str:
    """Reading-order page text minus headers/footers, cleaned.

    Paragraphs follow typographic blocks: a big vertical gap, a font
    change, or a list/reference marker starts a new paragraph. Sentence
    boundaries never split paragraphs — front-matter lines (which end
    without punctuation) must stay separate from body text.
    """
    kept = [ln for ln in layout.lines if _keep_line(layout, ln)]
    paragraphs: list[str] = []
    for group in _group_lines(kept):
        paragraphs.extend(block_to_paragraphs(group))
    return "\n\n".join(paragraphs)


def _keep_line(layout: PageLayout, ln: DocLine) -> bool:
    from app.services.text_clean import normalize_line

    norm = normalize_line(ln.text)
    if norm in layout.header_texts or norm in layout.footer_texts:
        return False
    # Standalone page numbers in the footer band.
    height = layout.height or 1.0
    if re.fullmatch(r"\d{1,4}", ln.text.strip()) and ln.y0 > height * _FOOTER_BAND:
        return False
    return True


_LIST_MARKER = re.compile(r"^(\[\d+\]|\(\d+\)|\d{1,3}[.\)\]]|•|-)\s*\S")


def block_to_paragraphs(block_lines: list[DocLine]) -> list[str]:
    """Split a typographic block's lines into true paragraphs."""
    from app.services.text_clean import clean_text, fix_wrap_hyphens

    text = fix_wrap_hyphens("\n".join(ln.text for ln in block_lines))
    paragraphs: list[str] = []
    current: list[str] = []
    for raw in text.split("\n"):
        stripped = raw.strip()
        if not stripped:
            continue
        if current and _LIST_MARKER.match(stripped):
            paragraphs.append(" ".join(current))
            current = [stripped]
        else:
            current.append(stripped)
    if current:
        paragraphs.append(" ".join(current))
    return [clean_text(p) for p in paragraphs if clean_text(p)]


def assemble_paragraphs(lines: list, body_size: float) -> str:
    """Join flat reading-order lines into paragraphs.

    `lines` elements need .text/.gap/.size/.bold (DocLine or _Flat).
    Breaks mirror block detection: vertical gaps, font changes, and
    list/reference markers. Sentence boundaries never split.
    """
    from app.services.text_clean import clean_text, fix_wrap_hyphens

    if not lines:
        return ""
    groups: list[list[str]] = [[lines[0].text]]
    for prev, ln in zip(lines, lines[1:]):
        new_para = (
            ln.gap > body_size * 1.6
            or abs(ln.size - prev.size) > 2.5
            or ln.bold != prev.bold
            or bool(_LIST_MARKER.match(ln.text.strip()))
        )
        if new_para:
            groups.append([ln.text])
        else:
            groups[-1].append(ln.text)
    out = []
    for group in groups:
        text = fix_wrap_hyphens("\n".join(group))
        text = re.sub(r"\s*\n\s*", " ", text)
        cleaned = clean_text(text)
        if cleaned:
            out.append(cleaned)
    return "\n\n".join(out)


def lines_to_blocks(lines: list[DocLine]) -> list[Block]:
    """Group consecutive lines into blocks (split on large gaps)."""
    return [_make_block(group) for group in _group_lines(lines)]


def _group_lines(lines: list[DocLine]) -> list[list[DocLine]]:
    if not lines:
        return []
    sizes = sorted(ln.size for ln in lines if ln.size > 0)
    median_size = sizes[len(sizes) // 2] if sizes else 10.0
    groups: list[list[DocLine]] = []
    current: list[DocLine] = []
    for ln in lines:
        if current and (
            ln.gap_before > median_size * 1.6
            or abs(ln.size - current[-1].size) > 2.5
            or ln.bold != current[-1].bold
        ):
            groups.append(current)
            current = [ln]
        else:
            current.append(ln)
    if current:
        groups.append(current)
    return groups


def _make_block(group: list[DocLine]) -> Block:
    return Block(
        text=" ".join(ln.text for ln in group),
        bbox=[
            min(ln.x0 for ln in group),
            min(ln.y0 for ln in group),
            max(ln.x1 for ln in group),
            max(ln.y1 for ln in group),
        ],
        font_size=round(sum(ln.size for ln in group) / len(group), 2),
        bold=all(ln.bold for ln in group),
    )
