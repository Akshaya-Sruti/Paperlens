"""Paper upload / retrieval routes."""

from __future__ import annotations

import os
from dataclasses import asdict
from typing import Literal
from uuid import UUID, uuid4

import fitz
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel, ValidationError

from app.ai.context import prepare_paper_context
from app.ai.openai_provider import get_provider
from app.ai.provider import AnalysisRequest, ProviderError as AIProviderError
from app.ai.schemas import AnalysisRecord, PaperAnalysis
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
from app.utils.storage import (
    load_analysis,
    load_paper,
    original_pdf_path,
    save_analysis,
    save_paper,
)

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
    record = load_analysis(settings.data_dir, normalized)
    if record and record.get("status") == "completed":
        stored["analysis_status"] = "completed"
        stored["analysis_updated_at"] = record.get("updated_at")
    elif record and record.get("status") == "failed":
        stored["analysis_status"] = "failed"
        stored["analysis_updated_at"] = record.get("updated_at")
    else:
        stored["analysis_status"] = "not_started"
        stored["analysis_updated_at"] = None
    return stored


class AnalyzeBody(BaseModel):
    force: bool = False


def _paper_or_404(paper_id: str) -> tuple[str, dict]:
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
    return normalized, stored


@router.get("/{paper_id}/analysis", response_model=AnalysisRecord)
async def get_analysis(paper_id: str):
    normalized, _ = _paper_or_404(paper_id)
    record = load_analysis(settings.data_dir, normalized)
    if record is None or record.get("status") != "completed":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No analysis exists for this paper yet. Generate one first.",
        )
    return record


@router.post("/{paper_id}/analyze", response_model=AnalysisRecord)
async def analyze_paper_route(paper_id: str, body: AnalyzeBody):
    normalized, stored = _paper_or_404(paper_id)

    existing = load_analysis(settings.data_dir, normalized)
    if (
        existing
        and existing.get("status") == "completed"
        and not body.force
    ):
        # Cached — no AI call.
        return existing

    if not stored.get("has_selectable_text", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This paper has no extractable text to analyze. "
            "OCR support will be added in a future version.",
        )

    context = prepare_paper_context(stored)
    if context.approx_input_chars < 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="There is not enough extracted content in this paper to analyze.",
        )

    provider = get_provider()
    try:
        raw = provider.analyze_paper(
            AnalysisRequest(
                paper_text=context.text,
                approx_input_chars=context.approx_input_chars,
                truncated=context.truncated,
                sections_included=context.sections_included,
            )
        )
    except AIProviderError as exc:
        _remember_failure(normalized, existing, str(exc))
        raise HTTPException(
            status_code=exc.status_code, detail=exc.message
        ) from exc

    try:
        analysis = PaperAnalysis.model_validate(raw)
    except ValidationError as exc:
        _remember_failure(
            normalized,
            existing,
            "The AI returned an unexpected format. Try again.",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The AI returned an unexpected format. Try again.",
        ) from exc

    analysis.meta.provider = provider.name
    analysis.meta.model = provider.model
    analysis.meta.truncated = context.truncated
    analysis.meta.sections_included = context.sections_included
    analysis.meta.approx_input_chars = context.approx_input_chars

    record = AnalysisRecord(status="completed", analysis=analysis)
    save_analysis(settings.data_dir, normalized, record.model_dump())
    return record.model_dump()


def _remember_failure(
    paper_id: str, existing: dict | None, message: str
) -> None:
    """Persist a failure marker — never overwriting a good analysis."""
    if existing and existing.get("status") == "completed":
        return
    record = AnalysisRecord(status="failed", analysis=None, error=message)
    try:
        save_analysis(settings.data_dir, paper_id, record.model_dump())
    except OSError:
        pass


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
