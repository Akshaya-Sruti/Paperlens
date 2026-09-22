"""Internal paper document model.

Plain dataclasses used between services. The API layer converts
these to pydantic schemas (see app/schemas/paper.py). Keeping the
internal model free of web-framework types makes it easy to swap
the storage backend later without touching extraction logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Block:
    """A typographic text block in reading order."""

    text: str
    bbox: list[float] = field(default_factory=list)  # [x0, y0, x1, y1]
    font_size: float = 0.0
    bold: bool = False


@dataclass
class Page:
    page_number: int  # 1-based
    text: str
    width: float
    height: float
    blocks: list[Block] = field(default_factory=list)


@dataclass
class Figure:
    page: int
    bbox: list[float] | None = None
    number: str | None = None  # "1", "IV", ...
    caption: str | None = None


@dataclass
class Table:
    page: int
    bbox: list[float] | None = None
    rows: int | None = None
    cols: int | None = None
    number: str | None = None
    caption: str | None = None


@dataclass
class Equation:
    page: int
    text: str
    bbox: list[float] | None = None


@dataclass
class Section:
    id: str
    title: str  # display title, number prefix removed
    original_title: str  # raw heading line as extracted
    normalized_type: str  # e.g. "methodology", "other"
    number: str | None  # "3", "3.1", "IV", ...
    level: int
    parent_id: str | None
    children: list[str] = field(default_factory=list)
    start_page: int = 1
    end_page: int = 1
    content: str = ""


@dataclass
class Reference:
    raw_text: str
    index: int | None = None
    authors: list[str] = field(default_factory=list)
    title: str | None = None
    year: int | None = None
    doi: str | None = None


@dataclass
class Citation:
    text: str  # e.g. "[12]" or "(Smith et al., 2023)"
    style: str  # "numeric" or "author_year"
    page: int
    section_id: str | None
    position: int  # char offset within the section content (or page text)
    reference_index: int | None = None
    reference_indices: list[int] = field(default_factory=list)


@dataclass
class Author:
    name: str
    affiliation: str | None = None
    email: str | None = None


@dataclass
class Publication:
    venue: str | None = None
    volume: str | None = None
    issue: str | None = None
    page_range: str | None = None


@dataclass
class ConceptCandidate:
    term: str
    frequency: int
    pages: list[int] = field(default_factory=list)


@dataclass
class DocumentQuality:
    has_extractable_text: bool = True
    page_count: int = 0
    text_coverage: float = 0.0  # fraction of pages with >= 100 chars
    has_sections: bool = False
    has_references: bool = False
    has_abstract: bool = False
    is_probably_scanned: bool = False
    two_column: bool = False
    avg_chars_per_page: float = 0.0


@dataclass
class RawMetadata:
    title_raw: str | None = None
    author_raw: str | None = None
    subject: str | None = None
    keywords: str | None = None
    creator: str | None = None
    producer: str | None = None
    creation_date: str | None = None
    modification_date: str | None = None


@dataclass
class Paper:
    id: str
    filename: str
    title: str | None = None
    authors: list[Author] = field(default_factory=list)
    affiliations: list[str] = field(default_factory=list)
    raw_author_text: str | None = None
    year: int | None = None
    publication: Publication = field(default_factory=Publication)
    doi: str | None = None
    urls: list[str] = field(default_factory=list)
    abstract: str | None = None
    keywords: list[str] = field(default_factory=list)
    pages: list[Page] = field(default_factory=list)
    sections: list[Section] = field(default_factory=list)
    references: list[Reference] = field(default_factory=list)
    citations: list[Citation] = field(default_factory=list)
    figures: list[Figure] = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)
    equations: list[Equation] = field(default_factory=list)
    concept_candidates: list[ConceptCandidate] = field(default_factory=list)
    quality: DocumentQuality = field(default_factory=DocumentQuality)
    metadata: RawMetadata = field(default_factory=RawMetadata)
    has_selectable_text: bool = True
    status: str = "processed"
