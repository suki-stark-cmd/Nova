"""NovaSystem — the fully wired system and its builder.

Reverse-engineered from OpenJarvis `system/core.py` + `system/builder.py`.
This is the top-level orchestrator that wires all subsystems together.
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.config import NovaConfig, get_config
from core.events import EventBus, get_event_bus
from core.types import AgentResult, Message, Role
from engine.base import InferenceEngine
from engine.ollama import OllamaEngine
from tools.base import BaseTool, ToolExecutor

logger = logging.getLogger(__name__)


@dataclass
class NovaSystem:
    """Fully wired Nova system — the single source of truth.

    From OpenJarvis `system/core.py:JarvisSystem`.
    """

    config: NovaConfig
    bus: EventBus
    engine: InferenceEngine
    model: str
    agent_name: str = "native_react"
    tools: List[BaseTool] = field(default_factory=list)
    tool_executor: Optional[ToolExecutor] = None
    session_store: Any = None
    scheduler: Any = None

    def ask(self, query: str, **kwargs: Any) -> Dict[str, Any]:
        """Execute a query through the agent and return result dict."""
        from agents.native_react import NativeReActAgent
        from core.registry import AgentRegistry

        agent_cls = AgentRegistry.get(self.agent_name)
        agent = agent_cls(
            self.engine,
            self.model,
            bus=self.bus,
            tools=self.tools,
        )
        result = agent.run(query)
        return {
            "content": result.content,
            "tool_results": [
                {"tool_name": tr.tool_name, "content": tr.content, "success": tr.success}
                for tr in result.tool_results
            ],
            "turns": result.turns,
            "model": self.model,
        }

    def close(self) -> None:
        """Release resources."""
        if self.scheduler and hasattr(self.scheduler, "stop"):
            self.scheduler.stop()
        if self.session_store and hasattr(self.session_store, "close"):
            self.session_store.close()
        self.engine.close()

    def __enter__(self) -> NovaSystem:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()


class SystemBuilder:
    """Config-driven fluent builder for NovaSystem.

    From OpenJarvis `system/builder.py:SystemBuilder`.

    Usage:
        system = (
            SystemBuilder()
            .engine("ollama")
            .model("llama3.2:1b")
            .sessions(True)
            .scheduler(True)
            .build()
        )
    """

    def __init__(self, config: Optional[NovaConfig] = None) -> None:
        self._config = config or get_config()
        self._model: Optional[str] = None
        self._sessions_enabled: bool = False
        self._scheduler_enabled: bool = False
        self._bus: Optional[EventBus] = None

    def engine(self, key: str) -> SystemBuilder:
        """Select the inference engine (currently only 'ollama')."""
        return self

    def model(self, name: str) -> SystemBuilder:
        self._model = name
        return self

    def sessions(self, enabled: bool) -> SystemBuilder:
        self._sessions_enabled = enabled
        return self

    def scheduler(self, enabled: bool) -> SystemBuilder:
        self._scheduler_enabled = enabled
        return self

    def event_bus(self, bus: EventBus) -> SystemBuilder:
        self._bus = bus
        return self

    def build(self) -> NovaSystem:
        """Construct a fully wired NovaSystem."""
        config = self._config
        bus = self._bus or get_event_bus()
        model = self._model or config.intelligence.default_model

        # Engine
        engine = OllamaEngine(
            host=config.engine.ollama.host,
            timeout=config.engine.ollama.timeout,
        )
        if not engine.health():
            raise RuntimeError(
                "Ollama is not running. Start it with: ollama serve"
            )

        # Tools
        from tools.builtin import register_builtin_tools
        from tools.registry import tool_collection
        register_builtin_tools()
        tools = tool_collection.all()
        tool_executor = ToolExecutor(tools, bus=bus)

        # Sessions (optional)
        session_store = None
        if self._sessions_enabled:
            try:
                from sessions import SessionStore
                session_store = SessionStore()
            except Exception as exc:
                logger.warning("Failed to init sessions: %s", exc)

        # Scheduler (optional)
        task_scheduler = None
        if self._scheduler_enabled:
            try:
                from scheduler import SchedulerStore, TaskScheduler
                store = SchedulerStore()
                task_scheduler = TaskScheduler(store)
                task_scheduler.start()
            except Exception as exc:
                logger.warning("Failed to init scheduler: %s", exc)

        system = NovaSystem(
            config=config,
            bus=bus,
            engine=engine,
            model=model,
            agent_name=config.agent.default_agent,
            tools=tools,
            tool_executor=tool_executor,
            session_store=session_store,
            scheduler=task_scheduler,
        )
        return system


__all__ = ["NovaSystem", "SystemBuilder"]
