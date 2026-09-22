"""Application configuration from environment variables.

Stage 2 only: server, CORS and storage settings. No AI keys.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)
)))


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


settings = Settings()
