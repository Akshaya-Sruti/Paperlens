"""End-to-end PDF → structured Paper pipeline.

Stage 3 flow (deterministic, no AI):
    PDF → extraction → layout analysis → structure detection →
    metadata/entities → references/citations → canonical Paper model.
Later stages will consume the Paper model produced here.
"""

from __future__ import annotations

import fitz

from app.models.paper import (
    DocumentQuality,
    Paper,
    Publication,
)
from app.services import entity_service, layout_service, metadata_service, pdf_service
from app.services.layout_service import lines_to_blocks, page_text_clean
from app.services.reference_service import (
    detect_citations,
    link_author_year_citations,
    parse_references,
)
from app.services.section_service import build_structure
from app.utils.errors import ExtractionError, PdfError

# Below this much selectable text the PDF has no usable text layer.
_SCANNED_CHARS_PER_PAGE = 30
_SCANNED_MIN_CHARS = 100
# ...but a short text PDF (few words, no images) is still selectable
# text — only flag "scanned" when images suggest photographed pages.
_SCANNED_EMPTY_CHARS = 20


def _is_scanned(pdf: pdf_service.PdfDocument, total_chars: int) -> bool:
    threshold = max(_SCANNED_MIN_CHARS, _SCANNED_CHARS_PER_PAGE * len(pdf.pages))
    if total_chars >= threshold:
        return False
    if total_chars < _SCANNED_EMPTY_CHARS and pdf.pages_with_images > 0:
        return True
    return False


def process_pdf(paper_id: str, filename: str, data: bytes) -> Paper:
    pdf = pdf_service.open_pdf(data)
    try:
        doc: fitz.Document = pdf.doc
        raw_meta = metadata_service.extract_raw_metadata(doc)

        # Layout pass: reading order, headers/footers, columns.
        layouts, column_count = layout_service.analyze_document(doc)
        for page, layout in zip(pdf.pages, layouts):
            page.text = page_text_clean(layout)
            page.blocks = lines_to_blocks(layout.lines)[:300]

        total_chars = pdf_service.total_text_length(pdf.pages)
        scanned = _is_scanned(pdf, total_chars)
        has_text = not scanned

        full_text = "\n".join(p.text for p in pdf.pages)
        first_page_text = pdf.pages[0].text if pdf.pages else ""
        header_texts = layouts[0].header_texts if layouts else set()

        title = metadata_service.detect_title(doc, raw_meta, filename)
        year = metadata_service.detect_year(doc, raw_meta)

        if has_text:
            authors, affiliations, _emails, raw_author_text, skip_texts = (
                entity_service.extract_authors(
                    layouts[0], title, raw_meta.author_raw
                )
            )
            venue = entity_service.detect_venue(
                first_page_text, header_texts, layouts[0].footer_texts
            )
            volume, issue, page_range = entity_service.detect_volume_issue(
                first_page_text
            )
            doi = entity_service.detect_doi(full_text)
            urls = entity_service.detect_urls(full_text)
            keywords = entity_service.detect_keywords(
                full_text, raw_meta.keywords
            )
            structure = build_structure(layouts, skip_texts)
            references = parse_references(structure.references)
            citations = detect_citations(
                structure.sections,
                max((r.index or 0) for r in references) if references else 0,
            )
            link_author_year_citations(citations, references)

            image_boxes = _boxes_by_page(
                [(f.page, f.bbox) for f in pdf.figures]
            )
            table_boxes = _boxes_by_page(
                [(t.page, t.bbox) for t in pdf.tables if t.bbox]
            )
            caption_figs = entity_service.detect_figures(layouts, image_boxes)
            caption_tables = entity_service.detect_tables(layouts, table_boxes)
            figures = _merge_figures(pdf.figures, caption_figs)
            tables = _merge_tables(pdf.tables, caption_tables)
            equations = entity_service.detect_equations(layouts)
            boost = (title.split() if title else []) + keywords
            concepts = entity_service.extract_concepts(
                [(p.page_number, p.text) for p in pdf.pages], boost
            )
        else:
            authors, affiliations, raw_author_text = [], [], None
            venue = volume = issue = page_range = doi = None
            urls, keywords = [], []
            structure = None
            references, citations = [], []
            figures, tables, equations, concepts = (
                list(pdf.figures),
                list(pdf.tables),
                [],
                [],
            )

        quality = _build_quality(pdf, structure, column_count, scanned)

        return Paper(
            id=paper_id,
            filename=filename,
            title=title,
            authors=authors,
            affiliations=affiliations,
            raw_author_text=raw_author_text,
            year=year,
            publication=Publication(
                venue=venue, volume=volume, issue=issue, page_range=page_range
            ),
            doi=doi,
            urls=urls,
            abstract=structure.abstract if structure else None,
            keywords=keywords,
            pages=list(pdf.pages),
            sections=structure.sections if structure else [],
            references=references,
            citations=citations,
            figures=figures,
            tables=tables,
            equations=equations,
            concept_candidates=concepts,
            quality=quality,
            metadata=raw_meta,
            has_selectable_text=has_text,
            status="processed" if has_text else "scanned",
        )
    except Exception as exc:
        if isinstance(exc, PdfError):
            raise
        raise ExtractionError() from exc
    finally:
        pdf.close()


def _boxes_by_page(
    items: list[tuple[int, list[float] | None]],
) -> dict[int, list[list[float]]]:
    grouped: dict[int, list[list[float]]] = {}
    for page, box in items:
        if box and len(box) == 4:
            grouped.setdefault(page, []).append(box)
    return grouped


def _merge_figures(pdf_figs, caption_figs):
    """Prefer captioned detections; keep uncaptioned image boxes too."""
    merged = list(caption_figs)
    captioned_boxes = {tuple(f.bbox) for f in caption_figs if f.bbox}
    for fig in pdf_figs:
        key = tuple(fig.bbox) if fig.bbox else None
        if key is None or key not in captioned_boxes:
            merged.append(fig)
    return merged


def _merge_tables(pdf_tables, caption_tables):
    merged = list(caption_tables)
    captioned_boxes = {tuple(t.bbox) for t in caption_tables if t.bbox}
    for table in pdf_tables:
        key = tuple(table.bbox) if table.bbox else None
        if key is None or key not in captioned_boxes:
            if table.number is None and table.caption is None:
                # Bare detection without caption: keep rows/cols only.
                pass
            merged.append(table)
    return merged


def _build_quality(pdf, structure, column_count: int, scanned: bool) -> DocumentQuality:
    pages = pdf.pages
    n = len(pages)
    with_text = sum(1 for p in pages if len((p.text or "").strip()) >= 100)
    total_chars = pdf_service.total_text_length(pages)
    return DocumentQuality(
        has_extractable_text=not scanned,
        page_count=n,
        text_coverage=round(with_text / n, 3) if n else 0.0,
        has_sections=bool(structure and structure.sections),
        has_references=bool(structure and structure.references),
        has_abstract=bool(structure and structure.abstract),
        is_probably_scanned=scanned,
        two_column=column_count == 2,
        avg_chars_per_page=round(total_chars / n, 1) if n else 0.0,
    )
