"""Structured AI analysis schemas (Stage 5).

The provider must return JSON matching PaperAnalysis. Anything the
paper does not support stays null / empty / "Not explicitly stated" —
never invented. Evidence keeps every important claim traceable to a
page/section of the uploaded paper.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    claim: str = ""
    source_type: Literal["paper"] = "paper"
    page: int | None = None
    section: str | None = None
    text: str = ""


class RichBlock(BaseModel):
    """A statement grounded in the paper, plus optional AI interpretation."""

    text: str | None = None
    interpretation: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)


class ListBlock(BaseModel):
    items: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)


class KeyFinding(BaseModel):
    statement: str
    interpretation: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)


class AnalysisMeta(BaseModel):
    provider: str = "openai"
    model: str = ""
    truncated: bool = False
    sections_included: list[str] = Field(default_factory=list)
    approx_input_chars: int = 0
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class PaperAnalysis(BaseModel):
    summary: RichBlock = Field(default_factory=RichBlock)
    research_problem: RichBlock = Field(default_factory=RichBlock)
    objectives: ListBlock = Field(default_factory=ListBlock)
    methodology: RichBlock = Field(default_factory=RichBlock)
    dataset: RichBlock = Field(default_factory=RichBlock)
    models: ListBlock = Field(default_factory=ListBlock)
    results: RichBlock = Field(default_factory=RichBlock)
    limitations: ListBlock = Field(default_factory=ListBlock)
    future_work: ListBlock = Field(default_factory=ListBlock)
    contributions: ListBlock = Field(default_factory=ListBlock)
    key_findings: list[KeyFinding] = Field(default_factory=list)
    meta: AnalysisMeta = Field(default_factory=AnalysisMeta)


class AnalysisRecord(BaseModel):
    """What is persisted to analysis.json."""

    status: Literal["completed", "failed"] = "completed"
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    analysis: PaperAnalysis | None = None
    error: str | None = None
