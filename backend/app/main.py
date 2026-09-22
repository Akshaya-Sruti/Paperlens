"""PaperLens API — Stage 3: document intelligence."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.papers import router as papers_router
from app.utils.config import settings

app = FastAPI(title=settings.app_name, version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(papers_router)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "stage": "3"}
