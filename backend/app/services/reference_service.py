"""Reference parsing, in-text citation detection and linking.

Deterministic only: conservative regexes over preserved raw text.
Every parsed field is populated only when the pattern match is
unambiguous; raw_text is always kept.
"""

from __future__ import annotations

import re

from app.models.paper import Citation, Reference, Section

_YEAR = re.compile(r"\b((?:19|20)\d{2})\b")
_QUOTED_TITLE = re.compile(r'[“"]([^“”"]{8,250}?)[”"]')
_DOI = re.compile(r"\b10\.\d{4,9}/[^\s\"'<>]+", re.I)

_NUMERIC_CIT = re.compile(r"\[(\d+(?:\s*[,–—\-]\s*\d+)*)\]")
_AUTHOR_YEAR_CIT = re.compile(
    r"\(([^\W\d_][\w.'-]*(?:\s+et\s+al\.?)?(?:\s*,\s*[^\W\d_][\w.'-]*)*"
    r"(?:\s*;\s*[^\W\d_][\w.'-]*(?:\s+et\s+al\.?)?)*"
    r"\s*,?\s*((?:19|20)\d{2})[a-z]?(?:\s*;\s*(?:(?:19|20)\d{2})[a-z]?)*)\)"
)


def _clean_doi(raw: str) -> str:
    return raw.rstrip(".,;:)]}>\"'")


_NAME_PARTICLES = frozenset(
    {"de", "van", "von", "der", "den", "la", "le", "du", "et", "al", "da"}
)


def _valid_ref_author(name: str) -> bool:
    """Strict name check for reference author lists.

    Rejects title/venue fragments ("A seminal paper.", "Proc. TEST"):
    those contain lowercase words that are not name particles.
    """
    name = name.strip(" ,;")
    if not name or len(name) > 60:
        return False
    words = name.split()
    if not 1 <= len(words) <= 4:
        return False
    has_name_word = False
    for word in words:
        w = word.strip(".,")
        if not w:
            return False
        if (len(w) == 1 and w.isupper()) or re.fullmatch(r"[A-ZÀ-Þ]\.", word):
            has_name_word = True
            continue
        if w.lower() in _NAME_PARTICLES:
            continue
        if re.fullmatch(r"[A-ZÀ-Þ][A-Za-z.'-]*", w):
            if w.isupper() and len(w) > 3:
                return False  # "TEST", "PROC" — venue fragments
            has_name_word = True
            continue
        return False
    return has_name_word


def _split_author_block(head: str) -> list[str]:
    head = re.sub(r"^\s*[\[\(]?\d{1,3}[\]\)\.]?\s*", "", head.strip())
    if not head or len(head) > 400:
        return []
    # Authors come first: consume sentence chunks while they are all
    # name-like, and stop at the first chunk that is not (title/venue).
    authors: list[str] = []
    for chunk in re.split(r"(?<=\.)\s+", head):
        subs = [
            s.strip(" ,;")
            for s in re.split(r"\s+and\s+|;\s*|,\s*", chunk)
            if s.strip(" ,;")
        ]
        if subs and all(_valid_ref_author(s) for s in subs):
            authors.extend(subs)
        else:
            break
        if len(authors) >= 10:
            break
    return authors[:10]


def parse_reference(ref: Reference) -> Reference:
    """Fill structured fields where the raw text allows it."""
    raw = ref.raw_text
    doi_match = _DOI.search(raw)
    if doi_match:
        ref.doi = _clean_doi(doi_match.group(0))

    years = [int(y) for y in _YEAR.findall(raw)]
    if years:
        # The publication year is usually the last 4-digit year... but
        # page ranges ("pp. 1-10, 2019") confuse this; prefer a year
        # near the end that is not part of a larger number.
        ref.year = years[-1] if 1900 <= years[-1] <= 2100 else None

    title_match = _QUOTED_TITLE.search(raw)
    if title_match:
        candidate = title_match.group(1).strip()
        if len(candidate.split()) >= 3:
            ref.title = candidate

    # Authors: text before the year (or before the quoted title).
    anchor = title_match.start() if title_match else -1
    if anchor < 0 and years:
        anchor = raw.rfind(str(ref.year)) if ref.year else -1
    head = raw[:anchor] if anchor > 0 else ""
    head = re.sub(r"^\s*[\[\(]?\d{1,3}[\]\)\.]?\s*", "", head)
    authors = _split_author_block(head)
    # Only accept when the head looks like a name list (has periods or
    # commas suggesting initials/surnames) to avoid garbage.
    if authors and ("," in head or "." in head):
        ref.authors = authors[:10]
    return ref


def parse_references(refs: list[Reference]) -> list[Reference]:
    return [parse_reference(ref) for ref in refs]


def _expand_numeric_group(group: str) -> list[int]:
    """'[1, 3-5]' → [1, 3, 4, 5]. Ranges capped to avoid blowups."""
    out: list[int] = []
    for chunk in re.split(r"\s*,\s*", group.strip()):
        m = re.fullmatch(r"(\d+)\s*[–—\-]\s*(\d+)", chunk)
        if m:
            start, end = int(m.group(1)), int(m.group(2))
            if 0 < end - start <= 30 and start > 0:
                out.extend(range(start, end + 1))
            else:
                out.append(start)
        elif chunk.isdigit():
            out.append(int(chunk))
    return out[:40]


def detect_citations(
    sections: list[Section], max_ref_index: int
) -> list[Citation]:
    """Find in-text citations with page + section association."""
    citations: list[Citation] = []
    for section in sections:
        content = section.content or ""
        for match in _NUMERIC_CIT.finditer(content):
            indices = _expand_numeric_group(match.group(1))
            # Skip year-like brackets "[2020]" and huge indices.
            indices = [i for i in indices if 0 < i <= max(max_ref_index, 1) + 50]
            if not indices:
                continue
            if len(match.group(0)) > 40:
                continue
            valid = [i for i in indices if 1 <= i <= max_ref_index] if max_ref_index else []
            citations.append(
                Citation(
                    text=match.group(0),
                    style="numeric",
                    page=section.start_page,
                    section_id=section.id,
                    position=match.start(),
                    reference_index=valid[0] if valid else None,
                    reference_indices=valid,
                )
            )
        for match in _AUTHOR_YEAR_CIT.finditer(content):
            if len(match.group(0)) > 120:
                continue
            citations.append(
                Citation(
                    text=match.group(0),
                    style="author_year",
                    page=section.start_page,
                    section_id=section.id,
                    position=match.start(),
                    reference_index=None,
                    reference_indices=[],
                )
            )
    return citations[:5000]


def _surname(name: str) -> str:
    parts = re.sub(r"[.]", "", name).split()
    return parts[-1].lower() if parts else ""


def link_author_year_citations(
    citations: list[Citation], references: list[Reference]
) -> None:
    """Resolve (Author, Year) citations against parsed references."""
    by_key: dict[tuple[str, int], int] = {}
    for ref in references:
        if ref.index is None or not ref.year:
            continue
        for author in ref.authors:
            surname = _surname(author)
            if surname:
                by_key[(surname, ref.year)] = ref.index

    for cit in citations:
        if cit.style != "author_year" or cit.reference_index is not None:
            continue
        names = re.findall(r"[A-ZÀ-Þ][\w.'-]+", cit.text)
        year_match = _YEAR.search(cit.text)
        if not names or not year_match:
            continue
        year = int(year_match.group(1))
        for name in names:
            key = (name.lower().rstrip("s"), year)
            if key in by_key:
                cit.reference_index = by_key[key]
                cit.reference_indices = [by_key[key]]
                break
            if (name.lower(), year) in by_key:
                cit.reference_index = by_key[(name.lower(), year)]
                cit.reference_indices = [cit.reference_index]
                break
