"""Local file storage for processed papers.

Stage 2 only: each paper lives under
    <data_dir>/<paper_id>/paper.json  (+ original.pdf)
The route layer only depends on save_paper / load_paper, so a
database can replace this module later without touching services.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

_PAPER_ID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")


def paper_dir(data_dir: str, paper_id: str) -> str:
    if not _PAPER_ID_RE.match(paper_id):
        raise ValueError("Invalid paper id")
    return os.path.join(data_dir, "papers", paper_id)


def save_paper(data_dir: str, paper_id: str, paper: dict[str, Any], pdf_bytes: bytes) -> None:
    directory = paper_dir(data_dir, paper_id)
    os.makedirs(directory, exist_ok=True)
    tmp_json = os.path.join(directory, "paper.json.tmp")
    with open(tmp_json, "w", encoding="utf-8") as fh:
        json.dump(paper, fh, ensure_ascii=False)
    os.replace(tmp_json, os.path.join(directory, "paper.json"))
    with open(os.path.join(directory, "original.pdf"), "wb") as fh:
        fh.write(pdf_bytes)


def load_paper(data_dir: str, paper_id: str) -> dict[str, Any] | None:
    try:
        directory = paper_dir(data_dir, paper_id)
    except ValueError:
        return None
    path = os.path.join(directory, "paper.json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def original_pdf_path(data_dir: str, paper_id: str) -> str | None:
    """Filesystem path of the stored original PDF, if present."""
    try:
        directory = paper_dir(data_dir, paper_id)
    except ValueError:
        return None
    path = os.path.join(directory, "original.pdf")
    return path if os.path.isfile(path) else None
