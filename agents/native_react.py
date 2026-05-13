"""NativeReActAgent — Tool-calling loop agent using Ollama's native API.

Reverse-engineered from OpenJarvis `agents/native_react.py`.

KEY DIFFERENCE: OpenJarvis uses regex parsing of "Thought: / Action: / Action Input:"
text output. Nova uses Ollama's NATIVE tool calling API — the model returns structured
tool_calls directly, no string parsing needed. This is:
  1. More reliable (no regex failures)
  2. Faster (less prompt overhead)
  3. Better for small models like llama3.2:1b
"""

from __future__ import annotations
import json
import logging
import re
from typing import Any, Dict, List, Optional

from agents.base import BaseAgent
from core.config import get_config
from core.events import EventBus, get_event_bus
from core.registry import AgentRegistry
from core.types import AgentResult, Message, Role, ToolCall, ToolResult
from engine.ollama import OllamaEngine
from tools.base import BaseTool, ToolExecutor
from tools.builtin import register_builtin_tools
from tools.intent_router import route_intent
from tools.registry import tool_collection

logger = logging.getLogger(__name__)


def _parse_text_tool_calls(content: str) -> List[Dict[str, Any]]:
    """Fallback parser for when small models output tool calls as text.

    llama3.2:1b sometimes returns tool calls as JSON in the content field
    instead of using the structured tool_calls API. This parser handles
    patterns like:
      {"name": "get_time", "parameters": {}}
      [{"name": "get_weather", "parameters": {"city": "London"}}]
    """
    if not content or not content.strip():
        return []

    text = content.strip()

    # Try to extract JSON objects that look like tool calls
    patterns = [
        # Match {"name": "...", "parameters": {...}}
        r'\{\s*"name"\s*:\s*"([^"]+)"\s*,\s*"parameters"\s*:\s*(\{[^}]*\}|\[[^\]]*\])\s*\}',
        # Match {"name": "...", "arguments": {...}}
        r'\{\s*"name"\s*:\s*"([^"]+)"\s*,\s*"arguments"\s*:\s*(\{[^}]*\}|\[[^\]]*\])\s*\}',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            calls = []
            for i, (name, args_str) in enumerate(matches):
                try:
                    args = json.loads(args_str)
                    if isinstance(args, list):
                        args = {}
                    calls.append({
                        "id": f"text_call_{i}",
                        "name": name,
                        "arguments": json.dumps(args),
                    })
                except json.JSONDecodeError:
                    calls.append({
                        "id": f"text_call_{i}",
                        "name": name,
                        "arguments": "{}",
                    })
            return calls

    # Try parsing the entire content as JSON
    try:
        data = json.loads(text)
        if isinstance(data, dict) and "name" in data:
            args = data.get("parameters", data.get("arguments", {}))
            if isinstance(args, list):
                args = {}
            return [{
                "id": "text_call_0",
                "name": data["name"],
                "arguments": json.dumps(args) if isinstance(args, dict) else "{}",
            }]
        if isinstance(data, list):
            calls = []
            for i, item in enumerate(data):
                if isinstance(item, dict) and "name" in item:
                    args = item.get("parameters", item.get("arguments", {}))
                    if isinstance(args, list):
                        args = {}
                    calls.append({
                        "id": f"text_call_{i}",
                        "name": item["name"],
                        "arguments": json.dumps(args) if isinstance(args, dict) else "{}",
                    })
            return calls
    except json.JSONDecodeError:
        pass

    return []


@AgentRegistry.register("native_react")
class NativeReActAgent(BaseAgent):
    """ReAct agent using Ollama's native tool-calling API.

    Loop: User → Model (with tools) → Tool Call → Observation → Model → Final Answer

    Supports DUAL MODE:
    1. Structured tool_calls from Ollama API (preferred)
    2. Text-based fallback for small models like llama3.2:1b that sometimes
       output tool calls as JSON text in the content field
    """

    agent_id = "native_react"

    def __init__(
        self,
        engine: Optional[OllamaEngine] = None,
        model: Optional[str] = None,
        *,
        bus: Optional[EventBus] = None,
        max_turns: Optional[int] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[BaseTool]] = None,
    ) -> None:
        cfg = get_config()

        if engine is None:
            engine = OllamaEngine(
                host=cfg.engine.ollama.host,
                timeout=cfg.engine.ollama.timeout,
            )
        if model is None:
            model = cfg.intelligence.default_model
        if bus is None:
            bus = get_event_bus()

        super().__init__(
            engine, model,
            bus=bus,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        self._max_turns = max_turns or cfg.agent.max_turns

        # Register and collect ALL tools
        register_builtin_tools()
        if tools:
            for t in tools:
                try:
                    tool_collection.add(t)
                except ValueError:
                    # Tool already registered, skip
                    pass

        self._all_tools = tool_collection.all()
        self._tools = self._all_tools  # Full list for tool execution
        self._all_tool_map = {t.spec.name: t for t in self._all_tools}
        self._executor = ToolExecutor(self._all_tools, bus=bus)

        # Conversation history (sliding window for small context)
        self._history: List[Message] = []
        self._system_prompt = cfg.agent.system_prompt

        # Log setup
        try:
            tool_names = [t.spec.name for t in self._all_tools]
            print(f"  Agent: {self.agent_id} | Tools: {len(tool_names)} loaded")
            print(f"  Model: {model} | Max turns: {self._max_turns}")
        except Exception as e:
            print(f"  Agent: {self.agent_id} | Tools: (error listing) | Model: {model}")

    def _get_routed_tools(self, query: str) -> List[Dict[str, Any]]:
        """Select only relevant tools for this query using intent routing.

        The 1B model can only handle ~8 tool schemas in its 2048 context.
        Sending all 24 would overflow the context window and cause the model
        to ignore tool calls entirely.
        """
        routed_names = route_intent(query)
        routed_tools = [self._all_tool_map[n] for n in routed_names if n in self._all_tool_map]
        if not routed_tools:
            # Fallback: send just core tools
            routed_tools = [self._all_tool_map[n] for n in ["get_time", "get_weather", "calculator", "web_search"] if n in self._all_tool_map]
        schemas = [t.to_ollama_tool() for t in routed_tools]
        logger.info("Routed tools for query: %s", [t.spec.name for t in routed_tools])
        return schemas

    def run(self, input_text: str) -> AgentResult:
        """Execute the full ReAct loop.

        This is the structured version matching OpenJarvis's AgentResult interface.
        """
        self._emit_turn_start(input_text)

        # Intent routing: select only relevant tools for this query
        routed_schemas = self._get_routed_tools(input_text)
        routed_names = [s["function"]["name"] for s in routed_schemas]
        print(f"  [Router] Selected: {', '.join(routed_names)}")

        # Build message list
        messages = self._build_messages(input_text, self._history, self._system_prompt)

        all_tool_results: List[ToolResult] = []
        turns = 0

        for _turn in range(self._max_turns):
            turns += 1

            # Generate with ROUTED tools (not all 24)
            result = self._generate(messages, tools=routed_schemas)

            if "error" in result:
                self._emit_turn_end(turns=turns)
                return AgentResult(
                    content=f"I encountered an error: {result['error']}",
                    turns=turns,
                )

            content = result.get("content", "")
            tool_calls = result.get("tool_calls", [])

            # DUAL MODE: If no structured tool_calls, try parsing from text
            # (llama3.2:1b often outputs tool calls as JSON text)
            if not tool_calls and content:
                text_tool_calls = _parse_text_tool_calls(content)
                if text_tool_calls:
                    # Validate tool names against registered tools
                    valid_names = {t.spec.name for t in self._tools}
                    text_tool_calls = [tc for tc in text_tool_calls if tc["name"] in valid_names]
                    if text_tool_calls:
                        tool_calls = text_tool_calls
                        logger.info("Parsed %d tool call(s) from text content", len(tool_calls))
                        content = ""  # Clear the JSON content so it's not appended as text message

            # No tool calls → this is the final answer
            if not tool_calls:
                self._emit_turn_end(turns=turns)
                return AgentResult(
                    content=content,
                    tool_results=all_tool_results,
                    turns=turns,
                )

            # Execute each tool call
            # Append assistant message with the tool call
            raw_msg = result.get("message", {})
            messages.append(Message(role=Role.ASSISTANT, content=content, tool_calls=[
                ToolCall(id=tc["id"], name=tc["name"], arguments=tc["arguments"])
                for tc in tool_calls
            ]))

            for tc_data in tool_calls:
                tool_call = ToolCall(
                    id=tc_data["id"],
                    name=tc_data["name"],
                    arguments=tc_data["arguments"],
                )

                print(f"  [Tool] {tool_call.name}({tool_call.arguments})")
                tool_result = self._executor.execute(tool_call)
                all_tool_results.append(tool_result)
                print(f"  [Result] {tool_result.content[:200]}")

                # Append tool result as tool message
                messages.append(Message(
                    role=Role.TOOL,
                    content=str(tool_result.content),
                    name=tool_call.name,
                ))

        # Max turns exceeded
        self._emit_turn_end(turns=turns, max_turns_exceeded=True)
        return AgentResult(
            content="I reached the maximum number of steps. Here's what I found so far.",
            tool_results=all_tool_results,
            turns=turns,
        )

    def chat(self, user_input: str, tts_callback=None) -> str:
        """High-level chat interface used by the main loop.

        Maintains conversation history with a sliding window to stay
        within the small context of llama3.2:1b.
        """
        # Run the agent
        result = self.run(user_input)
        
        # Clean up hallucinated responses (model sometimes outputs JSON/code)
        response = self._clean_response(result.content)

        # Update history (keep it small for 1b model)
        self._history.append(Message(role=Role.USER, content=user_input))
        if response:
            self._history.append(Message(role=Role.ASSISTANT, content=response))

        # Trim history to last 10 messages (5 exchanges) for 2048 ctx window
        if len(self._history) > 10:
            self._history = self._history[-10:]

        return response

    def _clean_response(self, text: str) -> str:
        """Remove JSON/code artifacts and hallucinations from model output.
        
        llama3.2:1b sometimes outputs pseudo-JSON or code. Clean these up
        to return only natural language responses.
        """
        if not text:
            return ""
        
        import re
        
        # Remove JSON-like structures and tool outputs
        text = re.sub(r'\{[^}]*"name"\s*:\s*"[^"]*"[^}]*\}', '', text, flags=re.DOTALL)
        text = re.sub(r'\{\s*"[^"]*"[^}]*\}', '', text)
        
        # Remove code blocks and backticks
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'`[^`]*`', '', text)
        
        # Remove common model artifacts
        text = re.sub(r'json code here', '', text, flags=re.IGNORECASE)
        text = re.sub(r'json output.*?[}\]]', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'tool[s]? (?:result|call|executed|output|parameter|function)[:\s]*', '', text, flags=re.IGNORECASE)
        
        # Remove meta-commentary the model adds
        text = re.sub(r'you (?:asked|told|want|need|should|can|must|will).*?(?:\.|$)', '', text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'to help you.*?(?:\.|$)', '', text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'(?:here\'s|here is).*?(?:\.|$)', '', text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'for future.*?(?:\.|$)', '', text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'i can (?:only|not|\'t).*?(?:\.|$)', '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Remove "I'm sorry" + lengthy apology explanations (keep actual error info only)
        text = re.sub(r'i\'?m sorry,?\s+but\s+(?:that\'?s not|i can\'?t|i don\'?t|you need).*?(?:\.|$)', '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Remove overly verbose explanations starting with "You can try"
        text = re.sub(r'(?:you can|please|if you want).*?(?:\.|$)', '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Clean multiple spaces
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Remove leading sentence fragments
        text = re.sub(r'^(?:to |the |a |an )', '', text, flags=re.IGNORECASE)
        
        # If nothing left, return default
        if not text or len(text.strip()) < 3:
            return "Done."
        
        # Capitalize first letter
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        
        return text.strip()

    def reset_history(self):
        """Clear conversation history."""
        self._history.clear()
