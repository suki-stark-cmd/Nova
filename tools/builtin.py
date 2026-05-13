"""Built-in tools for Nova AI.

Reverse-engineered from OpenJarvis tools:
- calculator.py  → CalculatorTool (AST-safe math)
- web_search.py  → WebSearchTool (DuckDuckGo)
- shell_exec.py  → SystemCommandTool (subprocess)
Plus Nova-specific: WeatherTool, TimeTool, YouTubeTool
"""

from __future__ import annotations
import ast
import datetime
import math
import operator
import os
import re
import subprocess
import urllib.parse
import urllib.request
import webbrowser
from typing import Any

from core.types import ToolResult, ToolSpec
from tools.base import BaseTool
from tools.registry import tool_collection


# ═══════════════════════════════════════════════════════════════
# Weather Tool
# ═══════════════════════════════════════════════════════════════

class WeatherTool(BaseTool):
    """Get current weather for a city."""

    tool_id = "get_weather"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="get_weather",
            description="Get current weather for a city.",
            parameters={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"}
                },
                "required": ["city"],
            },
        )

    def execute(self, **params: Any) -> ToolResult:
        city = params.get("city", "")
        if not city:
            return ToolResult(tool_name="get_weather", content="No city provided.", success=False)
        try:
            q = urllib.parse.quote(city)
            req = urllib.request.Request(
                f"https://wttr.in/{q}?format=3",
                headers={"User-Agent": "Nova/1.0"},
            )
            with urllib.request.urlopen(req, timeout=5) as r:
                return ToolResult(tool_name="get_weather", content=r.read().decode().strip())
        except Exception as e:
            return ToolResult(tool_name="get_weather", content=f"Weather error: {e}", success=False)


# ═══════════════════════════════════════════════════════════════
# Time Tool
# ═══════════════════════════════════════════════════════════════

class TimeTool(BaseTool):
    """Get current local time and date."""

    tool_id = "get_time"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="get_time",
            description="Get current local time and date.",
            parameters={"type": "object", "properties": {}},
        )

    def execute(self, **params: Any) -> ToolResult:
        now = datetime.datetime.now()
        return ToolResult(
            tool_name="get_time",
            content=f"Time: {now.strftime('%I:%M %p')}, Date: {now.strftime('%A, %B %d, %Y')}",
        )


# ═══════════════════════════════════════════════════════════════
# YouTube Tool — DEPRECATED: Use YouTubeEdgeTool from media_control.py
# ═══════════════════════════════════════════════════════════════
# This class is kept for backward compatibility but should NOT be registered.
# The YouTubeEdgeTool in media_control.py is the official implementation.

class YouTubeTool(BaseTool):
    """DEPRECATED: Search and play a video/song on YouTube. Use YouTubeEdgeTool instead."""

    tool_id = "play_youtube_deprecated"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="play_youtube_deprecated",
            description="DEPRECATED — Use media_control.YouTubeEdgeTool instead.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query for YouTube"}
                },
                "required": ["query"],
            },
        )

    def execute(self, **params: Any) -> ToolResult:
        return ToolResult(
            tool_name="play_youtube_deprecated",
            content="This tool is deprecated. Use media_control.YouTubeEdgeTool instead.",
            success=False
        )


# ═══════════════════════════════════════════════════════════════
# Calculator Tool (from OpenJarvis calculator.py — AST-safe eval)
# ═══════════════════════════════════════════════════════════════

_BINOPS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARYOPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}
_MATH_FUNCS = {
    "abs": abs, "round": round, "min": min, "max": max,
    "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "pi": math.pi, "e": math.e, "ceil": math.ceil, "floor": math.floor,
}


def _safe_eval_node(node: ast.AST) -> Any:
    """Recursively evaluate an AST node using only whitelisted operations."""
    if isinstance(node, ast.Expression):
        return _safe_eval_node(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float, complex)):
            return node.value
        raise ValueError(f"Unsupported constant: {type(node.value).__name__}")
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _BINOPS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        return _BINOPS[op_type](_safe_eval_node(node.left), _safe_eval_node(node.right))
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _UNARYOPS:
            raise ValueError(f"Unsupported unary: {op_type.__name__}")
        return _UNARYOPS[op_type](_safe_eval_node(node.operand))
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in _MATH_FUNCS:
            raise ValueError(f"Unknown function: {getattr(node.func, 'id', '?')}")
        return _MATH_FUNCS[node.func.id](*[_safe_eval_node(a) for a in node.args])
    if isinstance(node, ast.Name) and node.id in _MATH_FUNCS:
        val = _MATH_FUNCS[node.id]
        if isinstance(val, (int, float)):
            return val
    raise ValueError(f"Unsupported expression: {type(node).__name__}")


class CalculatorTool(BaseTool):
    """Safe math calculator using AST evaluation (from OpenJarvis)."""

    tool_id = "calculator"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="calculator",
            description="Evaluate a mathematical expression safely. Supports arithmetic, sqrt, log, sin, cos, etc.",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Math expression (e.g. '2+3*4', 'sqrt(16)')",
                    }
                },
                "required": ["expression"],
            },
        )

    def execute(self, **params: Any) -> ToolResult:
        expr = params.get("expression", "")
        if not expr:
            return ToolResult(tool_name="calculator", content="No expression.", success=False)
        try:
            tree = ast.parse(expr, mode="eval")
            result = float(_safe_eval_node(tree.body))
            return ToolResult(tool_name="calculator", content=str(result))
        except (ZeroDivisionError, ValueError, SyntaxError, TypeError) as e:
            return ToolResult(tool_name="calculator", content=f"Error: {e}", success=False)


# ═══════════════════════════════════════════════════════════════
# Web Search Tool (from OpenJarvis web_search.py — DuckDuckGo)
# ═══════════════════════════════════════════════════════════════

class WebSearchTool(BaseTool):
    """Search the web using DuckDuckGo (no API key needed — laptop-friendly)."""

    tool_id = "web_search"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="web_search",
            description="Search the web for current information using DuckDuckGo.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query."},
                    "max_results": {
                        "type": "integer",
                        "description": "Max results (default 3).",
                    },
                },
                "required": ["query"],
            },
            timeout_seconds=15.0,
        )

    def execute(self, **params: Any) -> ToolResult:
        query = params.get("query", "")
        max_results = params.get("max_results", 3)
        if not query:
            return ToolResult(tool_name="web_search", content="No query.", success=False)
        try:
            from ddgs import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            if not results:
                return ToolResult(tool_name="web_search", content="No results found.")
            formatted = "\n\n".join(
                f"**{r.get('title', 'Untitled')}**\n{r.get('href', '')}\n{r.get('body', '')}"
                for r in results
            )
            return ToolResult(tool_name="web_search", content=formatted)
        except ImportError:
            return ToolResult(
                tool_name="web_search",
                content="ddgs not installed. pip install ddgs",
                success=False,
            )
        except Exception as e:
            return ToolResult(tool_name="web_search", content="Search unavailable.", success=False)


# ═══════════════════════════════════════════════════════════════
# System Command Tool (from OpenJarvis shell_exec.py)
# ═══════════════════════════════════════════════════════════════

class SystemCommandTool(BaseTool):
    """Execute a system command (limited to safe operations)."""

    tool_id = "system_command"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="system_command",
            description="Execute a system command and return output. Use for opening apps, checking system info, etc.",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Command to execute."},
                },
                "required": ["command"],
            },
            timeout_seconds=15.0,
        )

    def execute(self, **params: Any) -> ToolResult:
        command = params.get("command", "")
        if not command:
            return ToolResult(tool_name="system_command", content="No command.", success=False)

        # Block dangerous commands
        dangerous = ["rm -rf", "del /s", "format", "mkfs", "dd if=", ":(){"]
        for d in dangerous:
            if d in command.lower():
                return ToolResult(
                    tool_name="system_command",
                    content=f"Blocked dangerous command: {command}",
                    success=False,
                )

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=15,
            )
            output = ""
            if result.stdout:
                output += result.stdout[:5000]
            if result.stderr:
                output += f"\n[stderr] {result.stderr[:2000]}"
            return ToolResult(
                tool_name="system_command",
                content=output.strip() or "(no output)",
                success=result.returncode == 0,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(tool_name="system_command", content="Command timed out.", success=False)
        except Exception as e:
            return ToolResult(tool_name="system_command", content=f"Error: {e}", success=False)


# ═══════════════════════════════════════════════════════════════
# File Read Tool (from OpenJarvis file_read.py)
# ═══════════════════════════════════════════════════════════════

class FileReadTool(BaseTool):
    """Read file contents with size limits."""

    tool_id = "file_read"
    _MAX_SIZE = 1_048_576  # 1 MB

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="file_read",
            description="Read the contents of a file. Returns the text content.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file."},
                    "max_lines": {"type": "integer", "description": "Max lines to return (default: all)."},
                },
                "required": ["path"],
            },
        )

    def execute(self, **params: Any) -> ToolResult:
        from pathlib import Path as _Path
        file_path = params.get("path", "")
        if not file_path:
            return ToolResult(tool_name="file_read", content="No path provided.", success=False)
        path = _Path(file_path)

        # Block sensitive files
        from security import is_sensitive_file
        if is_sensitive_file(path):
            return ToolResult(tool_name="file_read", content=f"Access denied: sensitive file.", success=False)
        if not path.exists():
            return ToolResult(tool_name="file_read", content=f"File not found: {file_path}", success=False)
        if not path.is_file():
            return ToolResult(tool_name="file_read", content=f"Not a file: {file_path}", success=False)
        try:
            size = path.stat().st_size
            if size > self._MAX_SIZE:
                return ToolResult(tool_name="file_read", content=f"File too large: {size} bytes.", success=False)
            text = path.read_text(encoding="utf-8", errors="replace")
            max_lines = params.get("max_lines")
            if max_lines and max_lines > 0:
                text = "\n".join(text.splitlines()[:max_lines])
            return ToolResult(tool_name="file_read", content=text)
        except Exception as e:
            return ToolResult(tool_name="file_read", content=f"Error: {e}", success=False)


# ═══════════════════════════════════════════════════════════════
# File Write Tool (from OpenJarvis file_write.py)
# ═══════════════════════════════════════════════════════════════

class FileWriteTool(BaseTool):
    """Write content to files with safety checks."""

    tool_id = "file_write"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="file_write",
            description="Write content to a file. Supports write and append modes.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to write."},
                    "content": {"type": "string", "description": "Content to write."},
                    "mode": {"type": "string", "description": "'write' (default) or 'append'."},
                },
                "required": ["path", "content"],
            },
        )

    def execute(self, **params: Any) -> ToolResult:
        from pathlib import Path as _Path
        file_path = params.get("path", "")
        content = params.get("content", "")
        mode = params.get("mode", "write")
        if not file_path:
            return ToolResult(tool_name="file_write", content="No path provided.", success=False)

        from security import is_sensitive_file
        path = _Path(file_path)
        if is_sensitive_file(path):
            return ToolResult(tool_name="file_write", content="Access denied: sensitive file.", success=False)

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            if mode == "append":
                with open(path, "a", encoding="utf-8") as f:
                    f.write(content)
            else:
                path.write_text(content, encoding="utf-8")
            return ToolResult(tool_name="file_write", content=f"Written to {file_path}")
        except Exception as e:
            return ToolResult(tool_name="file_write", content=f"Error: {e}", success=False)


# ═══════════════════════════════════════════════════════════════
# Think Tool (from OpenJarvis think.py — reasoning scratchpad)
# ═══════════════════════════════════════════════════════════════

class ThinkTool(BaseTool):
    """Zero-cost reasoning scratchpad — echoes input for chain-of-thought."""

    tool_id = "think"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="think",
            description="A reasoning scratchpad. Think through a problem step by step. Input is echoed back.",
            parameters={
                "type": "object",
                "properties": {
                    "thought": {"type": "string", "description": "Your reasoning or thought process."},
                },
                "required": ["thought"],
            },
        )

    def execute(self, **params: Any) -> ToolResult:
        return ToolResult(tool_name="think", content=params.get("thought", ""))


# ═══════════════════════════════════════════════════════════════
# HTTP Request Tool (from OpenJarvis http_request.py)
# ═══════════════════════════════════════════════════════════════

class HttpRequestTool(BaseTool):
    """Make HTTP requests to external APIs."""

    tool_id = "http_request"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="http_request",
            description="Make an HTTP GET or POST request to a URL and return the response.",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to request."},
                    "method": {"type": "string", "description": "HTTP method (GET/POST). Default: GET."},
                    "body": {"type": "string", "description": "Optional request body for POST."},
                },
                "required": ["url"],
            },
            timeout_seconds=15.0,
        )

    def execute(self, **params: Any) -> ToolResult:
        url = params.get("url", "")
        method = params.get("method", "GET").upper()
        body = params.get("body")
        if not url:
            return ToolResult(tool_name="http_request", content="No URL provided.", success=False)

        try:
            req = urllib.request.Request(url, method=method, headers={"User-Agent": "Nova/1.0"})
            if body and method in ("POST", "PUT", "PATCH"):
                req.data = body.encode("utf-8")
                req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read().decode("utf-8", errors="replace")
                if len(content) > 10000:
                    content = content[:10000] + "\n[...truncated]"
                return ToolResult(tool_name="http_request", content=content)
        except Exception as e:
            return ToolResult(tool_name="http_request", content=f"Request error: {e}", success=False)


# ═══════════════════════════════════════════════════════════════
# Register All Built-in Tools
# ═══════════════════════════════════════════════════════════════

_registered = False

def register_builtin_tools():
    """Register all built-in tools with the tool collection."""
    global _registered
    if _registered:
        return
    _registered = True

    # ── Core tools (from OpenJarvis) ─────────────────────────
    tool_collection.add(WeatherTool())
    tool_collection.add(TimeTool())
    tool_collection.add(CalculatorTool())
    tool_collection.add(WebSearchTool())
    tool_collection.add(SystemCommandTool())
    tool_collection.add(FileReadTool())
    tool_collection.add(FileWriteTool())
    tool_collection.add(ThinkTool())
    tool_collection.add(HttpRequestTool())

    # ── Windows Controls ─────────────────────────────────────
    from tools.windows_control import (
        VolumeControlTool, BrightnessControlTool, AppLauncherTool,
        ScreenshotTool, LockScreenTool, WifiToggleTool,
        SystemInfoTool, WindowManageTool,
    )
    tool_collection.add(VolumeControlTool())
    tool_collection.add(BrightnessControlTool())
    tool_collection.add(AppLauncherTool())
    tool_collection.add(ScreenshotTool())
    tool_collection.add(LockScreenTool())
    tool_collection.add(WifiToggleTool())
    tool_collection.add(SystemInfoTool())
    tool_collection.add(WindowManageTool())

    # ── Media & Apple Controls ───────────────────────────────
    from tools.media_control import (
        MediaPlaybackTool, AppleMusicTool, EdgeBrowserTool,
        YouTubeEdgeTool, AppleNotesTool, AppleRemindersTool,
        AlarmTimerTool,
    )
    tool_collection.add(MediaPlaybackTool())
    tool_collection.add(AppleMusicTool())
    tool_collection.add(EdgeBrowserTool())
    tool_collection.add(YouTubeEdgeTool())   # YouTube tool (opens in Edge)
    tool_collection.add(AppleNotesTool())
    tool_collection.add(AppleRemindersTool())
    tool_collection.add(AlarmTimerTool())
    # NOTE: YouTubeTool from this module is deprecated, YouTubeEdgeTool is the official tool


