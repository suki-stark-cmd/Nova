"""System prompt builder with persona, memory, and user profile support.

Reverse-engineered from OpenJarvis `prompt/builder.py`.
Assembles system prompts with frozen prefix for cache stability.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import List, Optional, Tuple


class SystemPromptBuilder:
    """Assembles system prompts with persona/memory/user files.

    Supports:
    - Agent persona (soul.md)
    - Agent memory (memory.md)
    - User profile (user.md)
    - Session context injection
    - Previous state restoration
    """

    def __init__(
        self,
        agent_template: str,
        *,
        soul_path: str = "~/.nova/soul.md",
        memory_path: str = "~/.nova/memory.md",
        user_path: str = "~/.nova/user.md",
        soul_max_chars: int = 2000,
        memory_max_chars: int = 1500,
        user_max_chars: int = 1000,
        session_context: Optional[str] = None,
        previous_state: Optional[str] = None,
    ) -> None:
        self._agent_template = agent_template
        self._soul_path = soul_path
        self._memory_path = memory_path
        self._user_path = user_path
        self._soul_max_chars = soul_max_chars
        self._memory_max_chars = memory_max_chars
        self._user_max_chars = user_max_chars
        self._session_context = session_context
        self._previous_state = previous_state
        self._frozen_prefix: Optional[str] = None

    def build(self) -> str:
        """Build the final system prompt."""
        if self._frozen_prefix is None:
            self._frozen_prefix = self._agent_template
            self._frozen_prefix = self._build_frozen_prefix()
        parts = [self._frozen_prefix]
        if self._session_context:
            parts.append(f"\n\n## Session Context\n\n{self._session_context}")
        if self._previous_state:
            parts.append(f"\n\n## Previous State\n\n{self._previous_state}")
        return "".join(parts)

    def _build_frozen_prefix(self) -> str:
        sections: list[str] = [self._agent_template]

        soul = self._load_file(self._soul_path, self._soul_max_chars)
        if soul:
            sections.append(f"## Agent Persona\n\n{soul}")

        memory = self._load_file(self._memory_path, self._memory_max_chars)
        if memory:
            sections.append(f"## Agent Memory\n\n{memory}")

        user = self._load_file(self._user_path, self._user_max_chars)
        if user:
            sections.append(f"## User Profile\n\n{user}")

        return "\n\n".join(sections)

    @staticmethod
    def _load_file(path_str: str, max_chars: int) -> str:
        path = Path(path_str).expanduser()
        if not path.exists():
            return ""
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return ""
        if len(content) <= max_chars:
            return content
        # Head-tail truncation (70/20 split)
        head_size = int(max_chars * 0.7)
        tail_size = int(max_chars * 0.2)
        omitted = len(content) - head_size - tail_size
        return (
            content[:head_size]
            + f"\n\n[...truncated {omitted} chars...]\n\n"
            + content[-tail_size:]
        )


__all__ = ["SystemPromptBuilder"]
