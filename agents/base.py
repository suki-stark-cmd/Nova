"""Base agent ABC.

Reverse-engineered from OpenJarvis `agents/_stubs.py`.
Provides BaseAgent with event emission, message building, and generation helpers.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from core.config import get_config
from core.events import EventBus, EventType
from core.types import AgentResult, Message, Role
from engine.base import InferenceEngine


class BaseAgent(ABC):
    """Base class for all agent implementations.

    Provides concrete helper methods:
    - _emit_turn_start / _emit_turn_end — event bus
    - _build_messages — conversation + system prompt assembly
    - _generate — delegates to engine with stored defaults
    """

    agent_id: str = ""

    def __init__(
        self,
        engine: InferenceEngine,
        model: str,
        *,
        bus: Optional[EventBus] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> None:
        self._engine = engine
        self._model = model
        self._bus = bus

        cfg = get_config()
        self._temperature = temperature if temperature is not None else cfg.intelligence.temperature
        self._max_tokens = max_tokens if max_tokens is not None else cfg.intelligence.max_tokens
        self._num_ctx = cfg.intelligence.num_ctx

    def _emit_turn_start(self, input_text: str) -> None:
        if self._bus:
            self._bus.publish(
                EventType.AGENT_TURN_START,
                {"agent": self.agent_id, "input": input_text},
            )

    def _emit_turn_end(self, **data: Any) -> None:
        if self._bus:
            payload: Dict[str, Any] = {"agent": self.agent_id}
            payload.update(data)
            self._bus.publish(EventType.AGENT_TURN_END, payload)

    def _build_messages(
        self,
        input_text: str,
        history: List[Message],
        system_prompt: str,
    ) -> List[Message]:
        """Assemble the message list for a generate call."""
        messages: List[Message] = [Message(role=Role.SYSTEM, content=system_prompt)]
        messages.extend(history)
        messages.append(Message(role=Role.USER, content=input_text))
        return messages

    def _generate(self, messages: List[Message], **kwargs: Any) -> Dict[str, Any]:
        """Call engine.generate() with stored defaults."""
        if self._bus:
            self._bus.publish(
                EventType.INFERENCE_START,
                {"model": self._model, "engine": self._engine.engine_id},
            )

        result = self._engine.generate(
            messages,
            model=self._model,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            num_ctx=self._num_ctx,
            **kwargs,
        )

        if self._bus:
            self._bus.publish(
                EventType.INFERENCE_END,
                {
                    "model": self._model,
                    "content": result.get("content", ""),
                    "tool_calls": result.get("tool_calls", []),
                },
            )

        return result

    @abstractmethod
    def run(self, input_text: str) -> AgentResult:
        """Execute the agent and return an AgentResult."""

    @abstractmethod
    def chat(self, user_input: str, tts_callback=None) -> str:
        """High-level chat interface for the main loop."""
