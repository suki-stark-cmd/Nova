"""Ollama inference engine backend.

Reverse-engineered from OpenJarvis `engine/ollama.py`.
Uses the `ollama` Python library for native tool calling support
instead of raw HTTP (OpenJarvis uses httpx).
This is better for laptop deployment — simpler, fewer dependencies.
"""

from __future__ import annotations
import json
import logging
from typing import Any, Dict, List, Sequence

from core.registry import EngineRegistry
from core.types import Message, Role, message_to_dict
from engine.base import InferenceEngine

logger = logging.getLogger(__name__)


@EngineRegistry.register("ollama")
class OllamaEngine(InferenceEngine):
    """Ollama backend using the native Python library."""

    engine_id = "ollama"

    def __init__(self, host: str = "http://localhost:11434", timeout: float = 120.0):
        self._host = host
        self._timeout = timeout
        try:
            import ollama as _ollama
            self._client = _ollama.Client(host=host, timeout=timeout)
        except ImportError:
            raise ImportError(
                "ollama package not installed. Install with: pip install ollama"
            )

    def generate(
        self,
        messages: Sequence[Message],
        *,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 512,
        tools: list = None,
        num_ctx: int = 2048,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate a response using Ollama's native API with tool calling."""

        # Convert Message objects to dicts
        msg_dicts = []
        for m in messages:
            if isinstance(m, Message):
                d = message_to_dict(m)
                # Ollama expects tool_call arguments as dicts, not JSON strings
                for tc in d.get("tool_calls", []):
                    fn = tc.get("function", {})
                    args = fn.get("arguments")
                    if isinstance(args, str):
                        try:
                            fn["arguments"] = json.loads(args)
                        except (json.JSONDecodeError, TypeError):
                            pass
                msg_dicts.append(d)
            elif isinstance(m, dict):
                msg_dicts.append(m)

        options = {
            "temperature": temperature,
            "num_predict": max_tokens,
            "num_ctx": num_ctx,
        }

        try:
            response = self._client.chat(
                model=model,
                messages=msg_dicts,
                tools=tools if tools else None,
                options=options,
            )
        except Exception as e:
            logger.error("Ollama generate error: %s", e)
            return {"content": f"Error: {e}", "error": str(e)}

        # Parse response
        msg = response.get("message", {})
        content = msg.get("content", "")

        # Extract tool calls
        raw_tool_calls = msg.get("tool_calls", [])
        tool_calls = []
        if raw_tool_calls:
            for i, tc in enumerate(raw_tool_calls):
                fn = tc.get("function", {})
                raw_args = fn.get("arguments", {})
                tool_calls.append({
                    "id": f"call_{i}",
                    "name": fn.get("name", ""),
                    "arguments": (
                        json.dumps(raw_args) if isinstance(raw_args, dict) else str(raw_args)
                    ),
                })

        # Extract usage stats
        prompt_tokens = response.get("prompt_eval_count", 0)
        completion_tokens = response.get("eval_count", 0)

        result = {
            "content": content,
            "tool_calls": tool_calls,
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
            "model": response.get("model", model),
            "message": msg,  # Keep raw message for tool-call loop
        }
        return result

    def list_models(self) -> List[str]:
        try:
            response = self._client.list()
            models = response.get("models", [])
            return [m.get("name", m.get("model", "")) for m in models]
        except Exception as e:
            logger.warning("Failed to list models: %s", e)
            return []

    def health(self) -> bool:
        try:
            self._client.list()
            return True
        except Exception as e:
            logger.debug("Ollama health check failed: %s", e)
            return False

    def close(self) -> None:
        pass
