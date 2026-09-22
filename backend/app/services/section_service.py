"""Academic section detection (Stage 3).

Layout-aware, multi-signal heading detection over reading-ordered
lines — no ML, no LLM. Tolerates numbered, unnumbered, roman-numeral
and ALL-CAPS styles across conference/journal layouts. Uncertain
layouts yield fewer sections, never invented ones.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.models.paper import Reference, Section
from app.services.layout_service import PageLayout, assemble_paragraphs
from app.services.text_clean import normalize_line

# ---------------------------------------------------------------------------
# Section type normalisation (deterministic keyword rules).
# ---------------------------------------------------------------------------

# (type, keywords) in priority order. Keywords match whole words.
_TYPE_RULES: list[tuple[str, list[str]]] = [
    ("abstract", ["abstract"]),
    ("references", ["references", "bibliography"]),
    ("acknowledgements", ["acknowledgement", "acknowledgment"]),
    ("future_work", ["future work", "future direction", "future research"]),
    ("conclusion", ["conclusion", "concluding remark", "summary"]),
    ("limitations", ["limitation"]),
    ("introduction", ["introduction", "motivation", "overview"]),
    ("related_work", [
        "related work", "related literature", "prior work",
        "previous work", "literature review", "literature survey",
        "state of the art",
    ]),
    ("background", ["background", "preliminar"]),
    ("dataset", ["dataset", "data collection", "benchmark", "corpus", "data"]),
    ("experiments", [
        "experiment", "evaluation", "implementation", "experimental",
        "setup", "ablation", "baseline",
    ]),
    ("results", ["result", "finding", "analysis", "performance"]),
    ("discussion", ["discussion"]),
    ("methodology", [
        "methodology", "method", "proposed", "approach", "framework",
        "architecture", "model", "algorithm", "technique", "material",
    ]),
]

_SUBSECTION_TYPES = {"dataset"}


def _word_hit(haystack: str, keyword: str) -> bool:
    # Optional trailing "s" so "result" also matches "results".
    pattern = r"\b" + re.escape(keyword).replace(r"\ ", r"\s+") + r"s?\b"
    return re.search(pattern, haystack) is not None


def normalize_section_type(title: str) -> str:
    norm = re.sub(r"[^a-z\s]", " ", title.lower())
    norm = re.sub(r"\s+", " ", norm).strip()
    for type_name, keywords in _TYPE_RULES:
        if any(_word_hit(norm, kw) for kw in keywords):
            return type_name
    return "other"


def display_title(number: str | None, rest: str) -> str:
    text = rest.strip().rstrip(".:").strip()
    if not text:
        return text
    if text.isupper():
        text = text.title()
        # Fix title-cased acronyms back is overkill; keep simple.
    return text


# ---------------------------------------------------------------------------
# Heading matching.
# ---------------------------------------------------------------------------

_ARABIC = re.compile(r"^(\d+(?:\.\d+)*)\s*[.\)\:]?\s+(.+?)\s*$")
_ROMAN = re.compile(r"^([IVXLCDM]{1,6})\.?\s+(.+?)\s*$", re.I)
_LETTER = re.compile(r"^([A-Z])[\.\)]\s+(.+?)\s*$")
_ABSTRACT_INLINE = re.compile(r"(?i)^\s*abstract\s*[:—–.\-]\s*(.+?)\s*$")
_REF_MARKER = re.compile(r"^\s*(?:\[\d+\]|\(\d+\)|\d+\s*[.)\]])\s*\S")
_ROMAN_SET = {"I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
              "XI", "XII", "XIII", "XIV", "XV"}


@dataclass
class _Heading:
    line_index: int
    page: int
    title: str  # display title
    original: str  # raw heading line
    number: str | None
    normalized_type: str
    level: int
    inline_rest: str = ""


@dataclass
class _Flat:
    page: int
    text: str
    size: float
    bold: bool
    gap: float
    y0: float
    in_header_footer: bool


def _flatten_layouts(layouts: list[PageLayout]) -> list[_Flat]:
    flat: list[_Flat] = []
    for layout in layouts:
        for ln in layout.lines:
            norm = normalize_line(ln.text)
            skip = norm in layout.header_texts or norm in layout.footer_texts
            flat.append(
                _Flat(
                    page=layout.page_number,
                    text=ln.text.strip(),
                    size=ln.size,
                    bold=ln.bold,
                    gap=ln.gap_before,
                    y0=ln.y0,
                    in_header_footer=skip,
                )
            )
    return flat


def _footnote_indices(
    layouts: list[PageLayout], flat: list[_Flat], body_size: float
) -> set[int]:
    """Page-1 footnote blocks (e.g. author-contribution notes).

    Small type at the bottom of the first page is front matter, not
    section body. Restricted to page 1 so small-font reference lists
    elsewhere are never eaten. Excluded lines stay in page text/raw
    views — nothing is deleted.
    """
    if not layouts:
        return set()
    height = layouts[0].height or 1.0
    # Flat indices of page-1 lines.
    page1 = [(i, ln) for i, ln in enumerate(flat) if ln.page == 1]
    small_bottom = [
        (i, ln)
        for i, ln in page1
        if ln.y0 > height * 0.72 and 0 < ln.size < body_size * 0.95
    ]
    if len(small_bottom) < 2:
        return set()
    # Keep only the trailing contiguous run (footnotes sit at the bottom).
    run: set[int] = set()
    for i, _ in reversed(small_bottom):
        if not run:
            run.add(i)
            continue
        if max(run) - i <= 3:  # allow small ordering gaps
            run.add(i)
        else:
            break
    return run if len(run) >= 2 else set()


def _body_metrics(flat: list[_Flat]) -> tuple[float, float]:
    sizes = [f.size for f in flat if f.page > 1 and f.size > 0]
    if not sizes:
        sizes = [f.size for f in flat if f.size > 0]
    if not sizes:
        return 10.0, 8.0
    ordered = sorted(sizes)
    body = ordered[len(ordered) // 2]
    gaps = sorted(f.gap for f in flat if f.gap > 0)
    median_gap = gaps[len(gaps) // 2] if gaps else 8.0
    return body, median_gap


def _looks_like_body_sentence(text: str) -> bool:
    words = text.split()
    return len(words) > 12 or (text.endswith(".") and len(words) > 7)


def _caps_ratio(text: str) -> float:
    """Fraction of words starting with an uppercase letter or digit."""
    words = text.split()
    if not words:
        return 0.0
    caps = sum(1 for w in words if w[:1].isupper() or w[:1].isdigit())
    return caps / len(words)


def _is_title_cased(text: str) -> bool:
    """Terse, mostly-capitalized — '3.1 Dataset', not table-row prose."""
    words = text.split()
    if not words or len(words) > 8:
        return False
    if not words[0][:1].isupper():
        return False
    caps = sum(1 for w in words if w[:1].isupper() or w[:1].isdigit())
    return caps / len(words) >= 0.6


def _match_heading(
    text: str, size: float, bold: bool, body_size: float
) -> tuple[str, str | None, str, int, str] | None:
    """Return (display, number, type, level, inline_rest) or None."""
    inline = _ABSTRACT_INLINE.match(text)
    if inline and len(inline.group(1).split()) >= 3:
        return "Abstract", None, "abstract", 1, inline.group(1).strip()

    big = size >= body_size * 1.12
    much_bigger = size >= body_size * 1.3

    arabic = _ARABIC.match(text)
    if arabic:
        number, rest = arabic.group(1), arabic.group(2).strip()
        depth = min(number.count(".") + 1, 3)
        if not rest or len(rest) > 90 or _looks_like_body_sentence(rest):
            return None
        dtype = normalize_section_type(rest)
        known = dtype not in ("other",)
        if big or bold:
            return display_title(number, rest), number, dtype, depth, ""
        if re.search(r"\.\s+[A-ZÀ-Þ]", rest):
            # Sentence break inside the line ("8 P100 GPUs. Even our ..."):
            # table-row prose, not a heading.
            return None
        if known and _caps_ratio(rest) >= 0.5 and len(rest.split()) <= 8:
            # "3.1 Encoder and Decoder Stacks" — but not table-row prose
            # like "4 The configuration of this model is".
            return display_title(number, rest), number, dtype, depth, ""
        # Unknown numbered lines only pass when terse and title-cased.
        if not known and _is_title_cased(rest):
            return display_title(number, rest), number, dtype, depth, ""
        return None

    roman = _ROMAN.match(text)
    if roman:
        numeral, rest = roman.group(1).upper(), roman.group(2).strip()
        if numeral in _ROMAN_SET and rest and len(rest) <= 80:
            dtype = normalize_section_type(rest)
            if dtype not in ("other",) or big or rest.isupper():
                return display_title(numeral, rest), numeral, dtype, 1, ""

    letter = _LETTER.match(text)
    if letter and len(text) <= 70:
        rest = letter.group(2).strip()
        dtype = normalize_section_type(rest)
        if dtype not in ("other",):
            return display_title(letter.group(1), rest), letter.group(1), dtype, 1, ""

    norm = normalize_line(text).rstrip(".:")
    dtype = normalize_section_type(text)
    # Unnumbered known headings ("Conclusion", "METHODOLOGY") still need
    # typographic evidence, or body phrases containing keywords
    # ("In contrast to ... models") would split the paper.
    if dtype not in ("other",) and len(text) <= 80:
        if big or bold or text.isupper() or _caps_ratio(text) >= 0.6:
            return display_title(None, text), None, dtype, 1, ""
        return None


def _score(text: str, size: float, bold: bool, gap: float,
           body_size: float, median_gap: float) -> float:
    score = 0.0
    if size >= body_size * 1.3:
        score += 2.0
    elif size >= body_size * 1.12:
        score += 1.5
    if bold:
        score += 1.0
    if text.isupper() and 2 <= len(text.split()) <= 8 and len(text) <= 60:
        score += 1.0
    if len(text) <= 70 and len(text.split()) <= 10:
        score += 1.0
    if gap > median_gap * 1.8:
        score += 1.0
    if text[:1].isupper():
        score += 0.5
    # Penalties.
    if len(text) > 90:
        score -= 4.0
    if _looks_like_body_sentence(text):
        score -= 3.0
    if text[:1].islower():
        score -= 2.0
    if _REF_MARKER.match(text) or "@" in text:
        score -= 4.0
    return score


def detect_headings(layouts: list[PageLayout]) -> tuple[list[_Heading], list[_Flat]]:
    flat = _flatten_layouts(layouts)
    body_size, median_gap = _body_metrics(flat)
    headings: list[_Heading] = []
    past_references = False

    for i, line in enumerate(flat):
        text = line.text
        if not text or line.in_header_footer:
            continue
        # Title/author zone at the very top of page 1.
        if line.page == 1 and i < 3:
            continue
        matched = _match_heading(text, line.size, line.bold, body_size)
        if matched is None:
            continue
        title, number, dtype, level, rest = matched

        if past_references and dtype not in ("references",):
            # Nothing but trailing matter follows the reference list.
            if dtype != "other" or "appendix" not in text.lower():
                continue
        if dtype == "references":
            past_references = True

        gate_score = _score(text, line.size, line.bold, line.gap, body_size, median_gap)
        has_number = number is not None
        known = dtype not in ("other",)
        big = line.size >= body_size * 1.12 or line.bold
        short = len(text) <= 70 and len(text.split()) <= 10
        if not (has_number or known or (big and short)):
            continue
        if gate_score < 2.5 and not (has_number and known):
            continue

        # Subsection inference for unnumbered lines.
        if number is None and level == 1 and dtype in _SUBSECTION_TYPES:
            if headings and headings[-1].level == 1:
                level = 2

        headings.append(
            _Heading(
                line_index=i, page=line.page, title=title, original=text,
                number=number, normalized_type=dtype, level=level,
                inline_rest=rest,
            )
        )

    # De-duplicate consecutive identical headings (running headers).
    deduped: list[_Heading] = []
    for heading in headings:
        if (
            deduped
            and deduped[-1].title == heading.title
            and heading.line_index - deduped[-1].line_index < 4
        ):
            continue
        deduped.append(heading)
    return deduped, flat


def _slug(title: str, used: set[str]) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "section"
    slug, n = base, 2
    while slug in used:
        slug = f"{base}-{n}"
        n += 1
    used.add(slug)
    return slug


@dataclass
class DocumentStructure:
    sections: list[Section] = field(default_factory=list)
    abstract: str | None = None
    references: list[Reference] = field(default_factory=list)


def build_structure(
    layouts: list[PageLayout], skip_texts: set[str] | None = None
) -> DocumentStructure:
    """Detect sections. skip_texts: normalized front-matter lines
    (title/authors/affiliations) excluded from body content."""
    headings, flat = detect_headings(layouts)
    structure = DocumentStructure()
    if not headings:
        return structure

    last_page = layouts[-1].page_number if layouts else 1
    used_slugs: set[str] = set()
    built: list[Section] = []
    body_size, _median_gap = _body_metrics(flat)
    footnotes = _footnote_indices(layouts, flat, body_size)

    for idx, heading in enumerate(headings):
        next_start = headings[idx + 1].line_index if idx + 1 < len(headings) else len(flat)
        skip = skip_texts or set()
        heading_y = flat[heading.line_index].y0
        body_lines = []
        for pos, ln in enumerate(flat[heading.line_index + 1 : next_start]):
            global_idx = heading.line_index + 1 + pos
            if ln.in_header_footer or global_idx in footnotes:
                continue
            if (
                ln.page == heading.page
                and ln.y0 < heading_y - 1.0
            ):
                # Visually above the heading on the same page: front
                # matter that flat ordering placed late (multi-column
                # author blocks). Never body content.
                continue
            if normalize_line(ln.text) == normalize_line(heading.original):
                continue
            if normalize_line(ln.text) in skip:
                continue
            body_lines.append(ln)
        if heading.inline_rest:
            # Inline "Abstract: ..." text becomes the first paragraph.
            first = _Flat(
                page=heading.page, text=heading.inline_rest, size=body_size,
                bold=False, gap=body_size * 2.0, y0=heading_y,
                in_header_footer=False,
            )
            body_lines.insert(0, first)
        content = assemble_paragraphs(body_lines, body_size)
        end_page = headings[idx + 1].page if idx + 1 < len(headings) else last_page

        if heading.normalized_type == "references":
            structure.references = _split_references(content)
            continue

        section = Section(
            id=_slug(heading.title, used_slugs),
            title=heading.title,
            original_title=heading.original,
            normalized_type=heading.normalized_type,
            number=heading.number,
            level=heading.level,
            parent_id=None,
            start_page=heading.page,
            end_page=max(heading.page, end_page),
            content=content,
        )
        built.append(section)
        if heading.normalized_type == "abstract" and structure.abstract is None:
            structure.abstract = content or None

    # Hierarchy: parent links + children lists.
    for i, section in enumerate(built):
        if section.level > 1:
            for prev in reversed(built[:i]):
                if prev.level == section.level - 1:
                    section.parent_id = prev.id
                    prev.children.append(section.id)
                    break
    structure.sections = built
    return structure


_MIDLINE_MARKER = re.compile(r"\s+(?=(?:\[\d{1,3}\]|\(\d{1,3}\))\s+[A-ZÀ-Þ])")


def _split_references(content: str) -> list[Reference]:
    if not content.strip():
        return []
    # Two-column reference lists can merge two entries into one flat
    # line ("[2] ... [9] ..."); split those on mid-line markers first.
    lines: list[str] = []
    for raw in content.splitlines():
        parts = _MIDLINE_MARKER.split(raw.strip())
        lines.extend(parts)
    entries: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current and not any(_REF_MARKER.match(l) for l in current):
                entries.append(current)
                current = []
            continue
        if _REF_MARKER.match(stripped) and current:
            entries.append(current)
            current = [stripped]
        else:
            current.append(stripped)
    if current:
        entries.append(current)
    refs = [
        Reference(raw_text=re.sub(r"\s+", " ", " ".join(e)).strip())
        for e in entries
        if " ".join(e).strip()
    ][:800]
    # Assign indices from explicit markers like "[12]" / "12.".
    for pos, ref in enumerate(refs, start=1):
        m = re.match(r"^\s*[\[\(]?(\d{1,3})[\]\)\.]", ref.raw_text)
        ref.index = int(m.group(1)) if m else pos
    return refs
