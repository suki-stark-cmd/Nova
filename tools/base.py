"""Base tool classes and executor.

Reverse-engineered from OpenJarvis `tools/_stubs.py`.
Provides BaseTool ABC, ToolExecutor dispatch engine, and tool description builder.
"""

from __future__ import annotations
import concurrent.futures
import json
import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

from core.events import EventBus, EventType
from core.types import ToolCall, ToolResult, ToolSpec


class BaseTool(ABC):
    """Base class for all tool implementations."""

    tool_id: str = ""

    @property
    @abstractmethod
    def spec(self) -> ToolSpec:
        """Return the tool specification."""

    @abstractmethod
    def execute(self, **params: Any) -> ToolResult:
        """Execute the tool with the given parameters."""

    def to_ollama_tool(self) -> Dict[str, Any]:
        """Convert to Ollama/OpenAI function-calling format."""
        s = self.spec
        return {
            "type": "function",
            "function": {
                "name": s.name,
                "description": s.description,
                "parameters": s.parameters,
            },
        }


class ToolExecutor:
    """Dispatch tool calls to registered tools.

    Reverse-engineered from OpenJarvis `tools/_stubs.py:ToolExecutor`.
    Handles argument parsing, timeout, and event emission.
    """

    def __init__(
        self,
        tools: List[BaseTool],
        bus: Optional[EventBus] = None,
        default_timeout: float = 30.0,
    ) -> None:
        self._tools: Dict[str, BaseTool] = {t.spec.name: t for t in tools}
        self._bus = bus
        self._default_timeout = default_timeout

    def execute(self, tool_call: ToolCall) -> ToolResult:
        """Parse arguments, dispatch to tool, measure latency, emit events."""
        tool = self._tools.get(tool_call.name)
        if tool is None:
            return ToolResult(
                tool_name=tool_call.name,
                content=f"Unknown tool: {tool_call.name}",
                success=False,
            )

        # Parse arguments
        try:
            params = json.loads(tool_call.arguments) if tool_call.arguments else {}
        except json.JSONDecodeError as exc:
            return ToolResult(
                tool_name=tool_call.name,
                content=f"Invalid arguments JSON: {exc}",
                success=False,
            )

        # Emit start event
        if self._bus:
            self._bus.publish(
                EventType.TOOL_CALL_START,
                {"tool": tool_call.name, "arguments": params},
            )

        # Execute with timeout
        timeout = tool.spec.timeout_seconds or self._default_timeout
        t0 = time.time()
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(tool.execute, **params)
                result = future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            result = ToolResult(
                tool_name=tool_call.name,
                content=f"Tool '{tool_call.name}' timed out after {timeout:.0f}s.",
                success=False,
            )
        except Exception as exc:
            result = ToolResult(
                tool_name=tool_call.name,
                content=f"Tool execution error: {exc}",
                success=False,
            )
        latency = time.time() - t0
        result.latency_seconds = latency

        # Emit end event
        if self._bus:
            self._bus.publish(
                EventType.TOOL_CALL_END,
                {
                    "tool": tool_call.name,
                    "success": result.success,
                    "latency": latency,
                },
            )

        return result

    def get_ollama_tools(self) -> List[Dict[str, Any]]:
        """Return tools in Ollama/OpenAI function-calling format."""
        return [t.to_ollama_tool() for t in self._tools.values()]

    def available_tools(self) -> List[ToolSpec]:
        """Return specs for all available tools."""
        return [t.spec for t in self._tools.values()]


def build_tool_descriptions(tools: List[BaseTool]) -> str:
    """Build rich text descriptions from a list of tools.

    From OpenJarvis `tools/_stubs.py:build_tool_descriptions`.
    """
    if not tools:
        return "No tools available."
    sections = []
    for t in tools:
        s = t.spec
        lines = [f"### {s.name}", s.description]
        props = s.parameters.get("properties", {})
        required = set(s.parameters.get("required", []))
        if props:
            lines.append("Parameters:")
            for pname, pinfo in props.items():
                ptype = pinfo.get("type", "any")
                req = ", required" if pname in required else ""
                desc = pinfo.get("description", "")
                lines.append(f"  - {pname} ({ptype}{req}): {desc}")
        sections.append("\n".join(lines))
    return "\n\n".join(sections)
