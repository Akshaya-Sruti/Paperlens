"""Pydantic schemas for API requests and responses.

These define the public contract consumed by the frontend.
Internal processing uses plain structures in services; only the
route layer converts to these schemas.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class PageBlock(BaseModel):
    text: str
    bbox: list[float] = Field(default_factory=list)
    font_size: float = 0.0
    bold: bool = False


class PaperPage(BaseModel):
    page_number: int
    text: str
    width: float
    height: float
    blocks: list[PageBlock] = Field(default_factory=list)


class PaperFigure(BaseModel):
    page: int
    bbox: list[float] | None = None
    number: str | None = None
    caption: str | None = None


class PaperTable(BaseModel):
    page: int
    bbox: list[float] | None = None
    rows: int | None = None
    cols: int | None = None
    number: str | None = None
    caption: str | None = None


class PaperEquation(BaseModel):
    page: int
    text: str
    bbox: list[float] | None = None


class PaperSection(BaseModel):
    id: str
    title: str
    original_title: str = ""
    normalized_type: str = "other"
    number: str | None = None
    level: int = 1
    parent_id: str | None = None
    children: list[str] = Field(default_factory=list)
    start_page: int
    end_page: int
    content: str


class PaperReference(BaseModel):
    raw_text: str
    index: int | None = None
    authors: list[str] = Field(default_factory=list)
    title: str | None = None
    year: int | None = None
    doi: str | None = None


class PaperCitation(BaseModel):
    text: str
    style: str
    page: int
    section_id: str | None = None
    position: int = 0
    reference_index: int | None = None
    reference_indices: list[int] = Field(default_factory=list)


class PaperAuthor(BaseModel):
    name: str
    affiliation: str | None = None
    email: str | None = None


class PaperPublication(BaseModel):
    venue: str | None = None
    volume: str | None = None
    issue: str | None = None
    page_range: str | None = None


class ConceptCandidate(BaseModel):
    term: str
    frequency: int
    pages: list[int] = Field(default_factory=list)


class DocumentQuality(BaseModel):
    has_extractable_text: bool = True
    page_count: int = 0
    text_coverage: float = 0.0
    has_sections: bool = False
    has_references: bool = False
    has_abstract: bool = False
    is_probably_scanned: bool = False
    two_column: bool = False
    avg_chars_per_page: float = 0.0


class PaperMetadata(BaseModel):
    title_raw: str | None = None
    author_raw: str | None = None
    subject: str | None = None
    keywords: str | None = None
    creator: str | None = None
    producer: str | None = None
    creation_date: str | None = None
    modification_date: str | None = None


class PaperResponse(BaseModel):
    id: str
    filename: str
    title: str | None = None
    authors: list[PaperAuthor] = Field(default_factory=list)
    affiliations: list[str] = Field(default_factory=list)
    raw_author_text: str | None = None
    year: int | None = None
    publication: PaperPublication = Field(default_factory=PaperPublication)
    doi: str | None = None
    urls: list[str] = Field(default_factory=list)
    abstract: str | None = None
    keywords: list[str] = Field(default_factory=list)
    page_count: int
    pages: list[PaperPage] = Field(default_factory=list)
    sections: list[PaperSection] = Field(default_factory=list)
    references: list[PaperReference] = Field(default_factory=list)
    citations: list[PaperCitation] = Field(default_factory=list)
    figures: list[PaperFigure] = Field(default_factory=list)
    tables: list[PaperTable] = Field(default_factory=list)
    equations: list[PaperEquation] = Field(default_factory=list)
    concept_candidates: list[ConceptCandidate] = Field(default_factory=list)
    quality: DocumentQuality = Field(default_factory=DocumentQuality)
    metadata: PaperMetadata = Field(default_factory=PaperMetadata)
    has_selectable_text: bool = True
    status: Literal["processed", "scanned"] = "processed"
    analysis_status: Literal["not_started", "completed", "failed"] = "not_started"
    analysis_updated_at: str | None = None


class UploadResponse(BaseModel):
    paper_id: str
    filename: str
    status: Literal["processed", "scanned"]


class ErrorResponse(BaseModel):
    detail: str
