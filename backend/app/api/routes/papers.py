"""Paper upload / retrieval routes."""

from __future__ import annotations

import os
from dataclasses import asdict
from typing import Literal
from uuid import UUID, uuid4

import fitz
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import Response

from app.schemas.paper import PaperResponse, UploadResponse
from app.services.pipeline import process_pdf
from app.utils.config import settings
from app.utils.errors import (
    CorruptedPdfError,
    EmptyPdfError,
    ExtractionError,
    PasswordProtectedPdfError,
    PdfError,
)
from app.utils.storage import load_paper, original_pdf_path, save_paper

router = APIRouter(prefix="/api/papers", tags=["papers"])

_PDF_MIME = "application/pdf"
_CHUNK_SIZE = 1024 * 1024


def _safe_filename(original: str | None) -> str:
    """Trust nothing about the client filename; keep a display-safe form."""
    name = os.path.basename((original or "").strip()) or "paper.pdf"
    name = "".join(ch for ch in name if ch.isprintable()).strip() or "paper.pdf"
    if len(name) > 120:
        stem, dot, ext = name.rpartition(".")
        name = (stem[:110] + dot + ext) if dot else name[:120]
    return name


async def _read_limited(upload: UploadFile) -> bytes:
    data = bytearray()
    while True:
        chunk = await upload.read(_CHUNK_SIZE)
        if not chunk:
            break
        data.extend(chunk)
        if len(data) > settings.max_upload_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File exceeds the 20 MB limit. Please choose a smaller PDF.",
            )
    return bytes(data)


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_paper(file: UploadFile | None = File(default=None)):
    if file is None or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file was provided. Please choose a PDF to upload.",
        )
    filename = _safe_filename(file.filename)
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported.",
        )
    if file.content_type and file.content_type != _PDF_MIME:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF files are supported.",
        )

    data = await _read_limited(file)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty. Try another PDF.",
        )

    paper_id = str(uuid4())
    try:
        paper = process_pdf(paper_id, filename, data)
    except PasswordProtectedPdfError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.user_message
        ) from exc
    except (CorruptedPdfError, EmptyPdfError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.user_message
        ) from exc
    except PdfError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=exc.user_message,
        ) from exc
    except Exception as exc:  # never leak internals
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong while reading this PDF. Try another file.",
        ) from exc

    save_paper(settings.data_dir, paper_id, asdict(paper), data)
    return UploadResponse(
        paper_id=paper_id, filename=filename, status=paper.status  # type: ignore[arg-type]
    )


@router.get("/{paper_id}", response_model=PaperResponse)
async def get_paper(paper_id: str):
    try:
        normalized = str(UUID(paper_id))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found. It may have been removed.",
        ) from None
    stored = load_paper(settings.data_dir, normalized)
    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found. It may have been removed.",
        )
    stored = dict(stored)
    stored["page_count"] = len(stored.get("pages", []))
    return stored


@router.get("/{paper_id}/media/{kind}/{index}/image")
async def media_image(
    paper_id: str, kind: Literal["figure", "table"], index: int
):
    """Render a detected figure/table region as PNG.

    The region is re-rendered from the stored original PDF — never raw
    embedded bytes — so nothing untrusted is executed or served blindly.
    Items without a reliable bounding box return 404 and the frontend
    falls back to "Figure detected on page X".
    """
    try:
        normalized = str(UUID(paper_id))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found."
        ) from None
    stored = load_paper(settings.data_dir, normalized)
    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found."
        )
    items = stored.get("figures" if kind == "figure" else "tables", [])
    if not isinstance(index, int) or index < 0 or index >= len(items):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No image is available for this item.",
        )
    item = items[index] or {}
    bbox = item.get("bbox")
    page_no = item.get("page")
    if (
        not isinstance(bbox, list)
        or len(bbox) != 4
        or not isinstance(page_no, int)
        or page_no < 1
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No image is available for this item.",
        )
    pdf_path = original_pdf_path(settings.data_dir, normalized)
    if pdf_path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No image is available for this item.",
        )
    try:
        doc = fitz.open(pdf_path)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not render this image. Try again later.",
        ) from exc
    try:
        if page_no > doc.page_count:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No image is available for this item.",
            )
        page = doc[page_no - 1]
        clip = fitz.Rect(*[float(v) for v in bbox])
        clip = clip & page.rect  # clamp to the page
        if clip.is_empty or clip.width < 8 or clip.height < 8:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No image is available for this item.",
            )
        # Cap output size: enough for reading, bounded for safety.
        zoom = min(2.0, 1400.0 / max(clip.width, clip.height))
        pix = page.get_pixmap(clip=clip, matrix=fitz.Matrix(zoom, zoom))
        png = pix.tobytes("png")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not render this image. Try again later.",
        ) from exc
    finally:
        try:
            doc.close()
        except Exception:
            pass
    return Response(
        content=png,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400"},
    )
