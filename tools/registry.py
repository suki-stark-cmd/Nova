"""Tool registry for Nova AI.

Simple registry that collects all tool instances.
Tools register themselves by import via the `register_builtin_tools()` function.
"""

from __future__ import annotations
from typing import Dict, List
from tools.base import BaseTool


class ToolCollection:
    """Collects and provides access to all registered tool instances."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def add(self, tool: BaseTool) -> None:
        """Add a tool instance to the collection. If tool with same name exists, raises ValueError."""
        if tool.spec.name in self._tools:
            raise ValueError(f"Tool '{tool.spec.name}' already registered")
        self._tools[tool.spec.name] = tool

    def get(self, name: str) -> BaseTool:
        return self._tools[name]

    def all(self) -> List[BaseTool]:
        return list(self._tools.values())

    def names(self) -> List[str]:
        return list(self._tools.keys())

    def clear(self) -> None:
        """Clear all registered tools (for testing)."""
        self._tools.clear()


# Module-level singleton
tool_collection = ToolCollection()
