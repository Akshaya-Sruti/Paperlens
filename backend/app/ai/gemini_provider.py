"""Google Gemini implementation of AIProvider.

Uses the official Google GenAI SDK with JSON response mode, one
automatic retry on malformed output, and classified ProviderErrors.
Mirrors OpenAIProvider's contract exactly: same input (section-aware
prompt/context), same output (validated dict), same safe logging —
never keys, prompts, paper contents, or request bodies.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.ai.prompts import (
    JSON_SCHEMA_HINT,
    SYSTEM_PROMPT,
    analysis_user_prompt,
)
from app.ai.provider import AIProvider, AnalysisRequest, ProviderError
from app.utils.config import settings

logger = logging.getLogger("paperlens.ai")

DEFAULT_MODEL = "gemini-2.5-flash"
MAX_OUTPUT_TOKENS = 8192
_FENCE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$")


class GeminiProvider(AIProvider):
    name = "gemini"

    def __init__(self, model: str | None = None, client: Any = None):
        self.model = model or settings.gemini_model or DEFAULT_MODEL
        self._client = client  # injected by tests; otherwise built lazily

    def analyze_paper(self, request: AnalysisRequest) -> dict:
        client = self._client or _build_client()
        prompt = (
            SYSTEM_PROMPT
            + "\n\n"
            + analysis_user_prompt(request.paper_text)
            + "\n\n"
            + JSON_SCHEMA_HINT
        )
        last_error: ProviderError | None = None
        for attempt in (1, 2):
            try:
                text = _generate(client, self.model, prompt)
                parsed = _parse_json(text)
                if not isinstance(parsed, dict):
                    raise ValueError("Model did not return a JSON object.")
                return parsed
            except ProviderError:
                raise
            except ValueError as exc:
                last_error = ProviderError(
                    "The AI returned an invalid response. Try again.",
                    kind="bad_response",
                    status_code=500,
                )
                prompt = (
                    prompt
                    + f"\n\nYour previous reply was not valid JSON. Error: {exc}. "
                    + "Reply with ONLY the JSON object."
                )
                if attempt == 2:
                    break
                continue
            except Exception as exc:
                _log_provider_error(exc, self.model)
                raise _classify(exc) from exc
        raise last_error or ProviderError(
            "The AI returned an invalid response. Try again.",
            kind="bad_response",
            status_code=500,
        )


def _build_client():
    try:
        from google import genai
    except ImportError as exc:
        raise ProviderError(
            "AI analysis is not available: the Gemini SDK is not installed.",
            kind="config",
            status_code=503,
        ) from exc
    api_key = settings.gemini_api_key
    if not api_key:
        raise ProviderError(
            "AI analysis is not configured: set GEMINI_API_KEY on the server and try again.",
            kind="config",
            status_code=503,
        )
    return genai.Client(api_key=api_key)


def _generate(client: Any, model: str, prompt: str) -> str:
    from google.genai import types

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            max_output_tokens=MAX_OUTPUT_TOKENS,
            temperature=0.2,
        ),
    )
    text = (getattr(response, "text", None) or "").strip()
    if not text:
        raise ValueError("Model returned an empty response.")
    return text


def _parse_json(text: str) -> Any:
    cleaned = _FENCE.sub("", text).strip()
    return json.loads(cleaned)


def _log_provider_error(exc: Exception, model: str) -> None:
    """Safe server-side diagnostic: error category, HTTP status, provider
    error code and request ID. Never logs keys, prompts, paper contents,
    headers, or request bodies.
    """
    status_code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    code = getattr(exc, "code", None)
    if isinstance(code, int):
        code = None  # numeric codes live in status_code; keep code textual
    request_id = getattr(exc, "request_id", None)
    detail = str(exc).replace("\n", " ")[:200]
    logger.warning(
        "AI provider error type=%s status=%s code=%s request_id=%s model=%s detail=%s",
        type(exc).__name__,
        status_code,
        code,
        request_id,
        model,
        detail,
    )


def _classify(exc: Exception) -> ProviderError:
    name = type(exc).__name__
    message = str(exc)
    lowered = f"{name} {message}".lower()
    status = getattr(exc, "status_code", None)
    code = str(getattr(exc, "code", "") or "").lower()

    def is_status(*codes: int) -> bool:
        return isinstance(status, int) and status in codes

    auth_markers = (
        "unauthenticated", "permission_denied", "invalid_api_key",
        "api key not valid", "api_key_invalid", "authentication",
        "invalid api key", "401", "403",
    )
    if (
        is_status(401, 403)
        or any(m in lowered for m in auth_markers)
        or any(m in code for m in ("unauthenticated", "permission_denied"))
    ):
        return ProviderError(
            "AI analysis is unavailable: the server's Gemini API key was rejected. "
            "Check GEMINI_API_KEY and try again.",
            kind="config",
            status_code=503,
        )

    quota_markers = (
        "insufficient_quota", "insufficient quota", "resource_exhausted",
        "quota_exceeded", "rate_limit", "rate limit", "429",
        "no credits remaining", "exceeded your current quota",
        "billing", "credit_balance_exhausted",
    )
    if (
        is_status(429)
        or any(m in lowered for m in quota_markers)
        or any(m in code for m in ("resource_exhausted",))
    ):
        text = (
            "the Gemini API quota for this key is exhausted or rate-limited"
            if any(
                m in lowered or m in code
                for m in ("quota", "exhausted", "billing", "credits")
            )
            else "Gemini is busy right now (rate limit)"
        )
        return ProviderError(
            f"AI analysis is unavailable: {text}. "
            "Check usage/quota in the Google AI dashboard, then try again.",
            kind="unavailable",
            status_code=503,
        )

    if "not_found" in lowered or "not found" in lowered or is_status(404):
        return ProviderError(
            "AI analysis is unavailable: the configured Gemini model is not "
            "available. Check GEMINI_MODEL and try again.",
            kind="config",
            status_code=503,
        )
    if "timeout" in lowered or "timed out" in lowered or "deadline" in lowered:
        return ProviderError(
            "AI analysis timed out. Try again.",
            kind="timeout",
            status_code=504,
        )
    if "connect" in lowered or "network" in lowered or "unavailable" in lowered:
        return ProviderError(
            "Could not reach the AI provider. Check the server connection and try again.",
            kind="unavailable",
            status_code=503,
        )
    return ProviderError(
        "AI analysis failed unexpectedly. Try again later.",
        kind="unavailable",
        status_code=500,
    )
