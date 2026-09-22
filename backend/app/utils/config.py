"""Application configuration from environment variables.

Loads backend/.env (if present) so local development needs no shell
exports; real environment variables always take precedence. No AI keys
are ever exposed outside this module's Settings object.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)
)))


def _load_local_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(os.path.join(_BACKEND_DIR, ".env"))


_load_local_env()


def _parse_origins(raw: str | None) -> list[str]:
    defaults = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    extra = (os.getenv("FRONTEND_URL") or "").strip()
    if extra and extra not in defaults:
        return [*defaults, extra]
    if raw:
        custom = [o.strip() for o in raw.split(",") if o.strip()]
        if custom:
            return custom
    return defaults


@dataclass(frozen=True)
class Settings:
    app_name: str = "PaperLens API"
    max_upload_bytes: int = 20 * 1024 * 1024
    data_dir: str = os.getenv(
        "PAPERLENS_DATA_DIR", os.path.join(_BACKEND_DIR, "data")
    )
    cors_origins: list[str] = field(
        default_factory=lambda: _parse_origins(os.getenv("CORS_ORIGINS"))
    )
    # Stage 5 AI settings. Backend-only — never send these to the frontend.
    ai_provider: str = os.getenv("AI_PROVIDER", "").strip() or "gemini"
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "").strip()
    openai_model: str = (
        os.getenv("OPENAI_MODEL", "").strip() or "gpt-4o-mini"
    )
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "").strip()
    gemini_model: str = (
        os.getenv("GEMINI_MODEL", "").strip() or "gemini-3.6-flash"
    )


settings = Settings()
