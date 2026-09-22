"""Low-level PDF access via PyMuPDF.

Responsibilities:
  - open PDF bytes safely (detect encryption / corruption / empty docs)
  - extract per-page text while preserving page boundaries + dimensions
  - record basic figure (image) and table locations (best-effort, optional)

No heuristics about titles, authors or sections live here — those
belong in metadata_service / section_service.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import fitz

from app.models.paper import Figure, Page, Table
from app.utils.errors import (
    CorruptedPdfError,
    EmptyPdfError,
    ExtractionError,
    PasswordProtectedPdfError,
)


@dataclass
class PdfDocument:
    """Thin wrapper keeping the fitz Document alongside extracted pages."""

    doc: fitz.Document
    pages: list[Page] = field(default_factory=list)
    figures: list[Figure] = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)
    pages_with_images: int = 0

    def close(self) -> None:
        try:
            self.doc.close()
        except Exception:
            pass


def open_pdf(data: bytes) -> PdfDocument:
    """Open PDF bytes and extract page text + media locations."""
    if not data[:5].startswith(b"%PDF-"):
        # Fast pre-check; fitz validation below is authoritative.
        raise CorruptedPdfError()

    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise CorruptedPdfError() from exc

    try:
        if doc.needs_pass:
            doc.close()
            raise PasswordProtectedPdfError()
        if doc.page_count == 0:
            doc.close()
            raise EmptyPdfError()

        result = PdfDocument(doc=doc)
        for i in range(doc.page_count):
            page = doc[i]
            try:
                text = page.get_text("text") or ""
            except Exception as exc:
                raise ExtractionError() from exc
            rect = page.rect
            result.pages.append(
                Page(
                    page_number=i + 1,
                    text=text,
                    width=float(rect.width),
                    height=float(rect.height),
                )
            )
        result.figures = _extract_figures(doc)
        result.tables = _extract_tables(doc)
        result.pages_with_images = _count_image_pages(doc)
        return result
    except (PasswordProtectedPdfError, EmptyPdfError, ExtractionError):
        raise
    except Exception as exc:
        try:
            doc.close()
        except Exception:
            pass
        raise ExtractionError() from exc


def _extract_figures(doc: fitz.Document) -> list[Figure]:
    """Best-effort image locations. Never fails the whole extraction."""
    figures: list[Figure] = []
    try:
        for i in range(doc.page_count):
            page = doc[i]
            try:
                images = page.get_images(full=True)
            except Exception:
                continue
            for img in images:
                try:
                    xref = img[0]
                    rects = page.get_image_rects(xref)
                except Exception:
                    continue
                for rect in rects:
                    # Skip tiny decorative images (icons / rules).
                    if rect.width < 40 or rect.height < 40:
                        continue
                    figures.append(
                        Figure(
                            page=i + 1,
                            bbox=[
                                float(rect.x0),
                                float(rect.y0),
                                float(rect.x1),
                                float(rect.y1),
                            ],
                        )
                    )
    except Exception:
        # Figures are optional metadata; ignore unexpected failures.
        pass
    return figures


def _extract_tables(doc: fitz.Document) -> list[Table]:
    """Best-effort table locations via PyMuPDF's table finder."""
    tables: list[Table] = []
    try:
        find_tables = getattr(fitz.Page, "find_tables", None)
        if find_tables is None:
            return tables
        for i in range(doc.page_count):
            page = doc[i]
            try:
                found = page.find_tables()
            except Exception:
                continue
            try:
                for table in found:
                    bbox = None
                    try:
                        rect = table.bbox
                        bbox = [
                            float(rect.x0),
                            float(rect.y0),
                            float(rect.x1),
                            float(rect.y1),
                        ]
                    except Exception:
                        bbox = None
                    rows = cols = None
                    try:
                        extracted = table.extract()
                        rows = len(extracted) if extracted else 0
                        cols = max((len(r) for r in extracted), default=0)
                    except Exception:
                        pass
                    tables.append(
                        Table(page=i + 1, bbox=bbox, rows=rows, cols=cols)
                    )
            finally:
                try:
                    found.close()
                except Exception:
                    pass
    except Exception:
        pass
    return tables


def _count_image_pages(doc: fitz.Document) -> int:
    """Pages containing any embedded raster image (unfiltered)."""
    count = 0
    try:
        for i in range(doc.page_count):
            try:
                if doc[i].get_images(full=True):
                    count += 1
            except Exception:
                continue
    except Exception:
        pass
    return count


def total_text_length(pages: list[Page]) -> int:
    return sum(len((p.text or "").strip()) for p in pages)
