"""Conservative text cleaning for extracted PDF text.

Fixes obvious extraction artefacts (hyphenated line wraps, repeated
whitespace) while preserving meaning. Never rewrites legitimate
hyphenated words: a wrap is only joined when the break is clearly
caused by line wrapping (lowercase letter + hyphen + newline +
lowercase letter).
"""

from __future__ import annotations

import re

_WS_RUN = re.compile(r"[ \t\u00a0]+")
_WRAP_HYPHEN = re.compile(r"([a-zà-öø-ÿ])-\n([a-zà-öø-ÿ])")
_MANY_NEWLINES = re.compile(r"\n{3,}")


def fix_wrap_hyphens(text: str) -> str:
    """Join words split by end-of-line hyphenation ("inter-\\nesting")."""
    return _WRAP_HYPHEN.sub(r"\1\2", text)


def normalize_whitespace(text: str) -> str:
    lines = [_WS_RUN.sub(" ", ln).strip() for ln in text.splitlines()]
    return _MANY_NEWLINES.sub("\n\n", "\n".join(lines)).strip()


def clean_text(text: str) -> str:
    if not text:
        return ""
    return normalize_whitespace(fix_wrap_hyphens(text))


def normalize_line(text: str) -> str:
    """Canonical form for comparing lines (headers/footers/headings)."""
    return re.sub(r"\s+", " ", text).strip().lower()
