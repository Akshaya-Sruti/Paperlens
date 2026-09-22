"""AI provider abstraction (Stage 5).

The application talks to AIProvider, never to a vendor SDK directly.
Swapping OpenAI for Gemini or a local model means adding a new
provider module — routes, pipeline and storage stay untouched.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ProviderError(Exception):
    """Classified provider failure (message is safe for the frontend)."""

    message: str
    kind: str = "unavailable"  # unavailable | timeout | bad_response | config
    status_code: int = 503

    def __str__(self) -> str:
        return self.message


@dataclass
class AnalysisRequest:
    paper_text: str
    approx_input_chars: int = 0
    truncated: bool = False
    sections_included: list[str] = field(default_factory=list)


class AIProvider(ABC):
    name: str = "base"
    model: str = ""

    @abstractmethod
    def analyze_paper(self, request: AnalysisRequest) -> dict:
        """Return the raw structured analysis as a plain dict.

        Raises ProviderError on any failure. Must never leak secrets;
        ProviderError messages are shown to users.
        """
        raise NotImplementedError
