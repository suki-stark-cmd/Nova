"""Canonical data types shared across all Nova primitives.

Reverse-engineered from OpenJarvis `core/types.py`.
Simplified to dataclasses suitable for a laptop-local assistant.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class Role(str, Enum):
    """Chat message roles (OpenAI/Ollama-compatible)."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class ToolCall:
    """A single tool invocation request from the model."""
    id: str
    name: str
    arguments: str  # JSON string


@dataclass
class Message:
    """A single chat message."""
    role: Role
    content: str = ""
    name: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None


@dataclass
class ToolResult:
    """Result returned by a tool invocation."""
    tool_name: str
    content: str
    success: bool = True
    latency_seconds: float = 0.0


@dataclass
class ToolSpec:
    """Declarative description of a tool's interface."""
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: float = 30.0


@dataclass
class AgentResult:
    """Result returned after an agent completes a run."""
    content: str
    tool_results: List[ToolResult] = field(default_factory=list)
    turns: int = 0


@dataclass
class Conversation:
    """Ordered list of messages with sliding-window cap."""
    messages: List[Message] = field(default_factory=list)
    max_messages: Optional[int] = None

    def add(self, message: Message) -> None:
        self.messages.append(message)
        if self.max_messages and len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]


def message_to_dict(msg: Message) -> Dict[str, Any]:
    """Serialize a Message to an Ollama-compatible dict."""
    d: Dict[str, Any] = {"role": msg.role.value, "content": msg.content}
    if msg.name:
        d["name"] = msg.name
    if msg.tool_calls:
        d["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.name, "arguments": tc.arguments},
            }
            for tc in msg.tool_calls
        ]
    if msg.tool_call_id:
        d["tool_call_id"] = msg.tool_call_id
    return d
