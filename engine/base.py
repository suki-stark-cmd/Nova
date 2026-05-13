"""ABC for inference engine backends.

Reverse-engineered from OpenJarvis `engine/_stubs.py`.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Sequence

from core.types import Message


class InferenceEngine(ABC):
    """Base class for all inference engine backends."""

    engine_id: str = ""

    @abstractmethod
    def generate(
        self,
        messages: Sequence[Message],
        *,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 512,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Synchronous completion — returns dict with 'content', 'usage', 'tool_calls'."""

    @abstractmethod
    def list_models(self) -> List[str]:
        """Return identifiers of models available on this engine."""

    @abstractmethod
    def health(self) -> bool:
        """Return True when the engine is reachable."""

    def close(self) -> None:
        """Release resources."""
        pass
