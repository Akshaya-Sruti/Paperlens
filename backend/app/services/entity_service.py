"""Entity extraction: authors, publication info, figures, tables,
equations, keywords and concept candidates.

All deterministic. Anything uncertain stays null/empty — the AI
stages will refine, not repair, this output.
"""

from __future__ import annotations

import re
from collections import Counter

from app.models.paper import Author
from app.services.layout_service import PageLayout
from app.services.text_clean import normalize_line

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
_ARXIV_LINE = re.compile(r"arxiv:\d", re.I)
_DOI = re.compile(r"\b10\.\d{4,9}/[^\s\"'<>]+", re.I)
_ARXIV_URL = re.compile(r"https?://arxiv\.org/(?:abs|pdf)/[\w./-]+", re.I)
_GENERIC_URL = re.compile(r"https?://[^\s\"'<>)]+", re.I)

_AFFILIATION_HINTS = (
    "university", "institute", "department", "college", "school",
    "laboratory", "laboratories", "centre", "center", "academy",
    "faculty", "polytechnic", "research", "lab", "labs", "brain",
    "inc", "corp", "ltd", "gmbh",
)

# Footnote/superscript markers stripped from author names (∗ † ‡ * 1 2 ³ …).
_FOOTNOTE_CHARS = "*†‡§¶∗0123456789⁰¹²³⁴⁵⁶⁷⁸⁹"


def _strip_footnotes(name: str) -> str:
    return name.strip(" ," + _FOOTNOTE_CHARS + ";")

_VENUE_PATTERNS = [
    re.compile(r"Proceedings of (?:the )?(.+?)(?:,|;|\(|\.|$)", re.I),
    re.compile(r"Published (?:in|by) (.+?)(?:,|;|\(|\.|$)", re.I),
    re.compile(r"\b(IEEE Transactions on [A-Za-z ]+?)(?:,|;|\(|\.|$)", re.I),
    re.compile(r"\b((?:International )?[A-Za-z &]*Journal of [A-Za-z &]+?)(?:,|;|\(|\.|$)", re.I),
]

_ACRONYM_VENUES = {
    "NEURIPS": "Conference on Neural Information Processing Systems",
    "NIPS": "Conference on Neural Information Processing Systems",
    "ICML": "International Conference on Machine Learning",
    "ICLR": "International Conference on Learning Representations",
    "ACL": "Annual Meeting of the Association for Computational Linguistics",
    "EMNLP": "Conference on Empirical Methods in Natural Language Processing",
    "CVPR": "Conference on Computer Vision and Pattern Recognition",
    "ICCV": "International Conference on Computer Vision",
    "ECCV": "European Conference on Computer Vision",
    "AAAI": "AAAI Conference on Artificial Intelligence",
    "IJCAI": "International Joint Conference on Artificial Intelligence",
    "KDD": "ACM SIGKDD Conference on Knowledge Discovery and Data Mining",
    "WWW": "International World Wide Web Conference",
    "SIGIR": "ACM SIGIR Conference on Research and Development in Information Retrieval",
    "ICDM": "IEEE International Conference on Data Mining",
}

_FIGURE_HEAD = re.compile(r"^(Figure|Fig\.)\s+([IVXLCDM\d]+)\s*[:.\-–]?\s*(.*)$", re.I)
_TABLE_HEAD = re.compile(r"^(Table|TABLE)\s+([IVXLCDM\d]+)\s*[:.\-–]?\s*(.*)$")
_MATH_CHARS = set("=<>+−-±×÷∑∫√∞∂∀∃∈^_{}\\/|~¬")

_KEYWORD_HEADS = ("keywords", "index terms", "key words")


# ---------------------------------------------------------------------------
# Authors + affiliations.
# ---------------------------------------------------------------------------

def _valid_name(name: str) -> bool:
    name = _strip_footnotes(re.sub(r"\s+", " ", name).strip())
    if not name or len(name) > 80:
        return False
    lowered = name.lower()
    if _AFFILIATION_RE.search(lowered):
        return False
    if "@" in name or "http" in lowered:
        return False
    if re.search(r"\d", name):
        return False
    words = name.split()
    if not 1 <= len(words) <= 4:
        return False
    for word in words:
        w = word.strip(".,").strip(_FOOTNOTE_CHARS)
        if not w:
            return False
        if len(w) == 1 and w.isupper():
            continue
        if re.fullmatch(r"\w\.", word, re.UNICODE) and word[0].isupper():
            continue  # initial, e.g. "J."
        if not w[0].isupper():
            return False
        if w.isupper() and len(w) > 4:
            return False  # "INTRODUCTION" is a heading, not a name
        if not re.fullmatch(r"[\w.'-]+", w, re.UNICODE):
            return False
    return True


def _split_names(chunk: str) -> list[str]:
    parts = re.split(
        r"\s*(?:;|\band\b|&)\s*|\s{2,},\s*|,\s*(?=\w[\w.'-]*\s+\w)",
        chunk,
    )
    names: list[str] = []
    for part in parts:
        cleaned = _strip_footnotes(re.sub(r"\s+", " ", part).strip())
        if cleaned and _valid_name(cleaned) and cleaned not in names:
            names.append(cleaned)
    return names


def _is_affiliation_line(text: str) -> bool:
    # Word boundaries: "available" must not match the "lab" hint.
    return _AFFILIATION_RE.search(text.lower()) is not None


_AFFILIATION_RE = re.compile(
    r"\b(universit\w*|institute\w*|department\w*|college\w*|school\w*|"
    r"laborator\w*|centers?|centres?|academy|academia|facult\w*|polytechnic\w*|"
    r"research|lab|labs|brain|inc\.?|corp\.?|ltd\.?|gmbh)\b"
)


def split_metadata_authors(raw_author: str | None) -> list[str]:
    if not raw_author:
        return []
    text = re.sub(r"\s+", " ", raw_author).strip()
    if ";" in text:
        chunks = text.split(";")
    elif re.search(r"\s+and\s+", text, re.I):
        chunks = re.split(r"\s+and\s+", text, flags=re.I)
    elif "," in text:
        pieces = [p.strip() for p in text.split(",") if p.strip()]
        chunks = pieces if len(pieces) > 2 else [text]
    else:
        chunks = [text]
    authors: list[str] = []
    for chunk in chunks:
        for name in _split_names(chunk):
            if name not in authors:
                authors.append(name)
    return authors[:20]


def extract_authors(
    layout: PageLayout,
    title: str | None,
    metadata_author: str | None,
) -> tuple[list[Author], list[str], list[str], str | None, set[str]]:
    """Order-independent author/affiliation classification.

    Front-matter author blocks are often multi-column, so top-of-page
    lines cannot be trusted to arrive in visual order. Every line in
    the top region is classified on its own merits instead.

    Returns (authors, affiliations, emails, raw_author_text, skip_texts)
    where skip_texts are normalized front-matter lines the section
    builder must exclude from body content.
    """
    from app.services.text_clean import normalize_line

    height = layout.height or 1.0
    region = [ln for ln in layout.lines if ln.y0 < height * 0.45]
    title_words = set((title or "").lower().split())

    def is_title_line(text: str) -> bool:
        words = text.lower().split()
        if not words or not title_words:
            return False
        hit = sum(1 for w in words if w.strip(".,:;") in title_words)
        return hit >= min(len(words), 2) and hit / len(words) >= 0.5

    zone = [
        ln
        for ln in region
        if not is_title_line(ln.text)
        and not _ARXIV_LINE.match(ln.text)
    ]
    raw_text = "\n".join(ln.text for ln in zone) or None
    emails = sorted({m.group(0) for ln in zone for m in _EMAIL.finditer(ln.text)})

    affiliations: list[str] = []
    name_lines: list[str] = []
    skip_texts: set[str] = set()
    for ln in zone:
        norm = normalize_line(ln.text)
        if _EMAIL.fullmatch(ln.text.strip()):
            skip_texts.add(norm)
            continue
        if _is_affiliation_line(ln.text):
            if ln.text not in affiliations:
                affiliations.append(ln.text)
            skip_texts.add(norm)
            continue
        # Short section-heading-like lines ("Abstract", "I. Introduction")
        # in the same region are structure, not authorship. Body-length
        # lines are left alone even if they contain keywords.
        from app.services.section_service import normalize_section_type

        if (
            len(ln.text) <= 80
            and len(ln.text.split()) <= 10
            and normalize_section_type(ln.text) != "other"
        ):
            skip_texts.add(norm)
            continue
        if len(ln.text) <= 180:
            name_lines.append(ln.text)

    shared_affiliation = "; ".join(affiliations) or None

    names: list[str] = []
    for line in name_lines:
        matched = False
        for name in _split_names(line):
            if name not in names:
                names.append(name)
            matched = True
        if matched:
            skip_texts.add(normalize_line(line))
        if len(names) >= 20:
            break

    from_meta = split_metadata_authors(metadata_author)
    if from_meta and not names:
        names = from_meta

    authors: list[Author] = []
    for name in names[:20]:
        email = None
        if emails:
            tokens = [
                re.sub(r"[.]", "", w).lower() for w in name.split() if len(w) > 1
            ]
            for candidate in emails:
                local = candidate.split("@")[0].lower().replace(".", "")
                if any(t and t in local for t in tokens):
                    email = candidate
                    break
            if email is None and len(emails) == 1 and len(names) == 1:
                email = emails[0]
        authors.append(
            Author(name=name, affiliation=shared_affiliation, email=email)
        )
    return authors, affiliations[:10], emails[:10], raw_text, skip_texts


# ---------------------------------------------------------------------------
# Publication info, DOI, URLs.
# ---------------------------------------------------------------------------

def detect_doi(full_text: str) -> str | None:
    for match in _DOI.finditer(full_text[:60000]):
        doi = match.group(0).rstrip(".,;:)]}>\"'")
        if "/" in doi and len(doi) < 120:
            # Skip reference-list DOIs on first hit? Prefer front matter.
            return doi
    return None


def detect_urls(full_text: str) -> list[str]:
    urls: list[str] = []
    for pattern in (_ARXIV_URL, _GENERIC_URL):
        for match in pattern.finditer(full_text[:60000]):
            url = match.group(0).rstrip(".,;:)]}\"'")
            if url not in urls and len(url) < 200:
                urls.append(url)
            if len(urls) >= 10:
                return urls
    return urls


def detect_venue(
    first_page_text: str, header_texts: set[str], footer_texts: set[str] | None = None
) -> str | None:
    # Match within single lines so a venue never absorbs the title block.
    haystacks = [
        ln.strip()
        for ln in first_page_text.splitlines()
        if ln.strip() and len(ln.strip()) <= 220
    ]
    haystacks.append(" ".join(sorted(header_texts))[:2000])
    if footer_texts:
        haystacks.append(" ".join(sorted(footer_texts))[:2000])
    for hay in haystacks:
        for pattern in _VENUE_PATTERNS:
            match = pattern.search(hay)
            if match:
                venue = re.sub(r"\s+", " ", match.group(1)).strip(" ,;")
                if "\n" in match.group(1):
                    continue
                if 4 <= len(venue) <= 120:
                    return venue
        acronym = re.search(
            r"\b(NeurIPS|NIPS|ICML|ICLR|ACL|EMNLP|CVPR|ICCV|ECCV|AAAI|IJCAI|KDD|WWW|SIGIR|ICDM)\b\s*(?:['’]?\d{2,4})?",
            hay,
        )
        if acronym:
            return _ACRONYM_VENUES.get(acronym.group(1).upper())
    return None


def detect_volume_issue(first_page_text: str) -> tuple[str | None, str | None, str | None]:
    head = first_page_text[:4000]
    volume = issue = page_range = None
    m = re.search(r"\b[Vv]ol(?:ume)?\.?\s*(\d{1,3})", head)
    if m:
        volume = m.group(1)
    m = re.search(r"\b(?:No|Issue|Iss)\.?\s*(\d{1,3})", head)
    if m:
        issue = m.group(1)
    m = re.search(r"\bpp?\.?\s*(\d{1,5})\s*[–—-]\s*(\d{1,5})", head)
    if m:
        page_range = f"{m.group(1)}–{m.group(2)}"
    return volume, issue, page_range


# ---------------------------------------------------------------------------
# Figures, tables, equations (captions + numbers + bboxes).
# ---------------------------------------------------------------------------

def _collect_caption(
    lines: list, start: int, rest: str
) -> tuple[str, float]:
    """Continuation lines must sit directly below the caption head, in
    the same column — otherwise body text from a neighbouring column
    gets absorbed into the caption."""
    head = lines[start]
    parts = [rest.strip()] if rest.strip() else []
    y = head.y0
    for nxt in lines[start + 1 : start + 4]:
        if len(nxt.text) > 180 or _FIGURE_OR_TABLE_HEAD.match(nxt.text.strip()):
            break
        if re.match(r"^\s*abstract\b", nxt.text, re.I):
            break
        if _looks_like_heading_start(nxt.text):
            break
        gap = nxt.y0 - head.y1 if hasattr(head, "y1") else nxt.y0 - y
        if gap < 0 or gap > 36:
            break
        if abs(nxt.x0 - head.x0) > 120:
            break
        parts.append(nxt.text.strip())
        head = nxt
    caption = re.sub(r"\s+", " ", " ".join(p for p in parts if p)).strip()
    return caption[:500], y


def _looks_like_heading_start(text: str) -> bool:
    """Continuation lines must not swallow the next section heading."""
    stripped = text.strip()
    if not stripped or len(stripped) > 80:
        return False
    if re.match(r"^([IVXLCDM]{1,6}\.?|\d+(?:\.\d+)*[.\)]?|[A-Z]\.)\s+\S", stripped):
        return True
    if stripped.isupper() and 2 <= len(stripped.split()) <= 8:
        return True
    return False


_FIGURE_OR_TABLE_HEAD = re.compile(r"^(Figure|Fig\.|Table|TABLE)\s+[IVXLCDM\d]+", re.I)


def detect_figures(
    layouts: list,
    image_boxes: dict[int, list[list[float]]],
) -> list:
    from app.models.paper import Figure

    figures: list[Figure] = []
    for layout in layouts:
        page_lines = layout.lines
        for i, ln in enumerate(page_lines):
            text = ln.text.strip()
            m = _FIGURE_HEAD.match(text)
            if not m:
                continue
            _kind, number, rest = m.group(1), m.group(2), m.group(3)
            caption, cap_y = _collect_caption(page_lines, i, rest)
            bbox = _nearest_box(image_boxes.get(layout.page_number, []), cap_y)
            figures.append(
                Figure(
                    page=layout.page_number,
                    bbox=bbox,
                    number=number.upper(),
                    caption=caption or None,
                )
            )
    return figures[:200]


def detect_tables(
    layouts: list,
    table_boxes: dict[int, list[list[float]]],
) -> list:
    from app.models.paper import Table

    tables: list[Table] = []
    for layout in layouts:
        page_lines = layout.lines
        for i, ln in enumerate(page_lines):
            text = ln.text.strip()
            m = _TABLE_HEAD.match(text)
            if not m:
                continue
            _kind, number, rest = m.group(1), m.group(2), m.group(3)
            caption, cap_y = _collect_caption(page_lines, i, rest)
            bbox = _nearest_box(table_boxes.get(layout.page_number, []), cap_y)
            tables.append(
                Table(
                    page=layout.page_number,
                    bbox=bbox,
                    number=number.upper(),
                    caption=caption or None,
                )
            )
    return tables[:200]


def _nearest_box(
    boxes: list[list[float]], y: float
) -> list[float] | None:
    best: list[float] | None = None
    best_dist = float("inf")
    for box in boxes:
        if len(box) != 4:
            continue
        center = (box[1] + box[3]) / 2
        dist = abs(center - y)
        if dist < best_dist:
            best, best_dist = box, dist
    return best


def detect_equations(layouts: list) -> list:
    from app.models.paper import Equation

    equations: list[Equation] = []
    for layout in layouts:
        for ln in layout.lines:
            text = ln.text.strip()
            if len(text) < 12 or len(text) > 400:
                continue
            numbered = re.search(r"\(\d{1,3}\)\s*$", text)
            symbols = sum(1 for ch in text if ch in _MATH_CHARS)
            letters = sum(1 for ch in text if ch.isalpha())
            if numbered and symbols >= 2:
                equations.append(
                    Equation(page=layout.page_number, text=text)
                )
            elif symbols >= 6 and symbols > letters and not text.endswith("."):
                equations.append(
                    Equation(page=layout.page_number, text=text)
                )
            if len(equations) >= 200:
                return equations
    return equations


# ---------------------------------------------------------------------------
# Keywords and concept candidates.
# ---------------------------------------------------------------------------

def detect_keywords(full_text: str, metadata_keywords: str | None) -> list[str]:
    found: list[str] = []
    head = full_text[:30000]
    for i, line in enumerate(head.splitlines()):
        m = re.match(
            r"^\s*(keywords|index terms|key words)\s*[:—–-]\s*(.+?)\s*$",
            line,
            re.I,
        )
        if m:
            rest = [m.group(2)]
            following = head.splitlines()[i + 1 : i + 2]
            if following and len(following[0]) < 200 and not re.match(
                r"^\s*(1\s|I\s|[A-Z][A-Z ]+$)", following[0]
            ):
                rest.append(following[0])
            for chunk in rest:
                for part in re.split(r"[,;·|]", chunk):
                    kw = re.sub(r"\s+", " ", part).strip(" .;")
                    if 1 < len(kw) <= 60 and kw.lower() not in [
                        k.lower() for k in found
                    ]:
                        found.append(kw)
            break
    if metadata_keywords:
        for part in re.split(r"[;\n]", metadata_keywords):
            for sub in part.split(","):
                kw = re.sub(r"\s+", " ", sub).strip(" -–—:;.")
                if (
                    1 < len(kw) <= 60
                    and kw.lower() not in [k.lower() for k in found]
                ):
                    found.append(kw if not kw.isupper() else kw.lower())
    return found[:12]


_STOPWORDS = frozenset(
    """
    the a an and or of to in on for with as by from at is are was were be been
    being this that these those it its their his her our your my his her which
    who whom whose what when where how why not no nor can will shall may might
    must should could would do does did done have has had having than then than
    such each other more most less least very only also into over under between
    both all any some few many much same so if else while during before after
    above below up down out off again further once here there their them they
    he she we you i me him us them his hers ours yours mine within without
    using used use uses based propose proposed method model paper work study
    result results show shown presentPresented section figure table et al via
    two one three first second new novel approach data based large small high
    low different several various twofold obtain obtained learning network
    arxiv doi http https fig figs figure figures table tables equation sections
    """.split()
)


def extract_concepts(
    pages_text: list[tuple[int, str]],
    boost_terms: list[str],
) -> list:
    from app.models.paper import ConceptCandidate

    word_pages: dict[str, set[int]] = {}
    word_counts: Counter[str] = Counter()
    bigram_counts: Counter[str] = Counter()
    bigram_pages: dict[str, set[int]] = {}

    for page_no, text in pages_text:
        words = re.findall(r"[a-z][a-z\-]{3,}", text.lower())
        for word in words:
            if word in _STOPWORDS or word.strip("-") != word:
                continue
            word_counts[word] += 1
            word_pages.setdefault(word, set()).add(page_no)
        for first, second in zip(words, words[1:]):
            if (
                first in _STOPWORDS
                or second in _STOPWORDS
                or len(first) < 4
                or len(second) < 4
            ):
                continue
            bigram = f"{first} {second}"
            bigram_counts[bigram] += 1
            bigram_pages.setdefault(bigram, set()).add(page_no)

    boost = {t.lower() for t in boost_terms if len(t) >= 4}
    candidates: list[ConceptCandidate] = []
    for word, count in word_counts.most_common(400):
        pages = word_pages[word]
        if count >= 3 and len(pages) >= 2:
            candidates.append(
                ConceptCandidate(
                    term=word, frequency=count, pages=sorted(pages)[:20]
                )
            )
        elif word in boost and count >= 2:
            candidates.append(
                ConceptCandidate(
                    term=word, frequency=count, pages=sorted(pages)[:20]
                )
            )
    for bigram, count in bigram_counts.most_common(200):
        if count >= 3 and len(bigram_pages[bigram]) >= 2:
            candidates.append(
                ConceptCandidate(
                    term=bigram,
                    frequency=count,
                    pages=sorted(bigram_pages[bigram])[:20],
                )
            )
    candidates.sort(key=lambda c: (-c.frequency, c.term))
    seen: set[str] = set()
    unique: list[ConceptCandidate] = []
    for cand in candidates:
        if cand.term not in seen:
            seen.add(cand.term)
            unique.append(cand)
        if len(unique) >= 30:
            break
    return unique
