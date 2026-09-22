"""OpenAI implementation of AIProvider (Stage 5).

Uses the official OpenAI SDK (chat completions + JSON mode) with one
automatic retry when the model returns invalid JSON. All SDK errors
are mapped to ProviderError with user-safe messages — raw provider
details and the API key never leave the backend.
"""

from __future__ import annotations

import json
import logging

from app.ai.prompts import (
    JSON_SCHEMA_HINT,
    SYSTEM_PROMPT,
    analysis_user_prompt,
)
from app.ai.provider import AIProvider, AnalysisRequest, ProviderError
from app.utils.config import settings

logger = logging.getLogger("paperlens.ai")

DEFAULT_MODEL = "gpt-4o-mini"
REQUEST_TIMEOUT_SECONDS = 120
MAX_RESPONSE_TOKENS = 4000


def _get_client():
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ProviderError(
            "AI analysis is not available: the OpenAI package is not installed.",
            kind="config",
            status_code=503,
        ) from exc
    api_key = settings.openai_api_key
    if not api_key:
        raise ProviderError(
            "AI analysis is not configured: set OPENAI_API_KEY on the server and try again.",
            kind="config",
            status_code=503,
        )
    return OpenAI(api_key=api_key, timeout=REQUEST_TIMEOUT_SECONDS)


class OpenAIProvider(AIProvider):
    name = "openai"

    def __init__(self, model: str | None = None):
        self.model = model or settings.openai_model or DEFAULT_MODEL

    def analyze_paper(self, request: AnalysisRequest) -> dict:
        client = _get_client()
        messages = self._messages(request.paper_text)
        last_error: ProviderError | None = None
        for attempt in (1, 2):
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    response_format={"type": "json_object"},
                    max_tokens=MAX_RESPONSE_TOKENS,
                    temperature=0.2,
                )
                content = (response.choices[0].message.content or "").strip()
                parsed = json.loads(content)
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
                messages = messages + [
                    {
                        "role": "user",
                        "content": (
                            "Your previous reply was not valid JSON. "
                            f"Error: {exc}. Reply with ONLY the JSON object."
                        ),
                    }
                ]
                if attempt == 2:
                    break
                continue
            except Exception as exc:
                _log_provider_error(exc, self.model)
                raise self._classify(exc) from exc
        raise last_error or ProviderError(
            "The AI returned an invalid response. Try again.",
            kind="bad_response",
            status_code=500,
        )

    def _messages(self, paper_text: str) -> list[dict]:
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": analysis_user_prompt(paper_text)
                + "\n\n"
                + JSON_SCHEMA_HINT,
            },
        ]

    @staticmethod
    def _classify(exc: Exception) -> ProviderError:
        name = type(exc).__name__
        message = str(exc)
        lowered = f"{name} {message}".lower()
        code = str(getattr(exc, "code", "") or "").lower()
        if "authentication" in lowered or "api key" in lowered or "401" in lowered:
            return ProviderError(
                "AI analysis is unavailable: the server's API key was rejected. "
                "Check OPENAI_API_KEY and try again.",
                kind="config",
                status_code=503,
            )
        quota_markers = ("insufficient_quota", "insufficient quota",
                         "credit_balance_exhausted", "billing_hard_limit_reached",
                         "no credits remaining", "exceeded your current quota")
        if any(m in lowered or m in code for m in quota_markers):
            return ProviderError(
                "AI analysis is unavailable: the OpenAI account has no remaining "
                "credit or quota. Check billing/quota in the OpenAI dashboard, "
                "then try again.",
                kind="unavailable",
                status_code=503,
            )
        if "rate limit" in lowered or "429" in lowered:
            return ProviderError(
                "AI analysis is busy right now (rate limit). Wait a minute and try again.",
                kind="unavailable",
                status_code=503,
            )
        if "timeout" in lowered or "timed out" in lowered:
            return ProviderError(
                "AI analysis timed out. Try again.",
                kind="timeout",
                status_code=504,
            )
        if "connect" in lowered or "network" in lowered:
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


def _log_provider_error(exc: Exception, model: str) -> None:
    """Safe server-side diagnostic: error category, HTTP status, provider
    error code and request ID. Never logs keys, headers, or request bodies.
    """
    status_code = getattr(exc, "status_code", None)
    code = getattr(exc, "code", None)
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
