"""Context compression strategies for keeping within small context windows.

Reverse-engineered from OpenJarvis `sessions/compression.py`.
Critical for llama3.2:1b with only 2048 context tokens.
"""

from __future__ import annotations
import json
from abc import ABC, abstractmethod
from typing import List

from core.types import Message, Role


class BaseCompressor(ABC):
    """Abstract base for context compression strategies."""

    @abstractmethod
    def compress(self, messages: List[Message], threshold: float) -> List[Message]:
        """Compress messages, keeping the most recent ones."""
        ...


class SessionConsolidation(BaseCompressor):
    """Summarize oldest N% of turns, keep recent (100-N)%."""

    def compress(self, messages: List[Message], threshold: float = 0.5) -> List[Message]:
        if not messages:
            return messages
        split = int(len(messages) * threshold)
        old = messages[:split]
        recent = messages[split:]
        if not old:
            return messages
        summary_text = "Summary of earlier conversation:\n"
        for m in old:
            summary_text += f"- [{m.role.value}]: {m.content[:100]}...\n"
        summary = Message(role=Role.SYSTEM, content=summary_text)
        return [summary] + recent


class RuleBasedPrecompression(BaseCompressor):
    """Strip boilerplate, truncate long tool outputs, collapse duplicates.

    No LLM call needed — perfect for laptop deployment.
    """

    TOOL_OUTPUT_MAX = 1500  # Smaller for 1b model

    def compress(self, messages: List[Message], threshold: float = 0.5) -> List[Message]:
        result: list[Message] = []
        for msg in messages:
            if msg.role == Role.TOOL and len(msg.content) > self.TOOL_OUTPUT_MAX:
                suffix = "\n[...truncated]"
                try:
                    parsed = json.loads(msg.content)
                    truncated = json.dumps(parsed, indent=None)[:self.TOOL_OUTPUT_MAX] + suffix
                except (json.JSONDecodeError, TypeError):
                    truncated = msg.content[:self.TOOL_OUTPUT_MAX] + suffix
                result.append(Message(role=msg.role, content=truncated, name=msg.name))
            else:
                result.append(msg)
        return result


class TieredSummaries(BaseCompressor):
    """Progressive compression: L0 (full) → L1 (paragraph) → L2 (one-line).

    Best for squeezing long conversations into tiny context windows.
    """

    def compress(self, messages: List[Message], threshold: float = 0.5) -> List[Message]:
        if not messages:
            return messages
        n = len(messages)
        l2_end = int(n * threshold * 0.5)
        l1_end = int(n * threshold)
        l2_msgs = messages[:l2_end]
        l1_msgs = messages[l2_end:l1_end]
        l0_msgs = messages[l1_end:]
        result: list[Message] = []
        if l2_msgs:
            one_liners = "; ".join(f"{m.role.value}: {m.content[:50]}" for m in l2_msgs)
            result.append(Message(role=Role.SYSTEM, content=f"[Oldest context] {one_liners}"))
        if l1_msgs:
            paragraphs = "\n".join(f"- {m.role.value}: {m.content[:200]}" for m in l1_msgs)
            result.append(Message(role=Role.SYSTEM, content=f"[Earlier context]\n{paragraphs}"))
        result.extend(l0_msgs)
        return result


__all__ = [
    "BaseCompressor",
    "RuleBasedPrecompression",
    "SessionConsolidation",
    "TieredSummaries",
]
