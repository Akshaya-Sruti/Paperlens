"""AI provider selection.

Single factory for the whole backend: routes call get_provider() and
receive the configured AIProvider. Switching vendors means setting
AI_PROVIDER (and the matching key) — no other code changes.
"""

from __future__ import annotations

from app.ai.provider import AIProvider


def get_provider(name: str | None = None) -> AIProvider:
    from app.utils.config import settings

    selected = (name or settings.ai_provider or "gemini").strip().lower()
    if selected == "openai":
        from app.ai.openai_provider import OpenAIProvider

        return OpenAIProvider()
    if selected == "gemini":
        from app.ai.gemini_provider import GeminiProvider

        return GeminiProvider()
    raise ValueError(
        f"Unknown AI provider {selected!r}. Set AI_PROVIDER to 'gemini' or 'openai'."
    )
