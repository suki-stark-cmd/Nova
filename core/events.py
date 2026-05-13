"""Thread-safe event bus for inter-component communication.

Reverse-engineered from OpenJarvis `core/events.py`.
Simplified to essential events for a laptop-local assistant.
"""

from __future__ import annotations
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class EventType(str, Enum):
    """Supported event categories."""
    INFERENCE_START = "inference_start"
    INFERENCE_END = "inference_end"
    TOOL_CALL_START = "tool_call_start"
    TOOL_CALL_END = "tool_call_end"
    AGENT_TURN_START = "agent_turn_start"
    AGENT_TURN_END = "agent_turn_end"


@dataclass
class Event:
    """A single event published on the bus."""
    event_type: EventType
    timestamp: float
    data: Dict[str, Any] = field(default_factory=dict)


Subscriber = Callable[[Event], None]


class EventBus:
    """Thread-safe publish/subscribe event bus."""

    def __init__(self) -> None:
        self._subscribers: Dict[EventType, List[Subscriber]] = {}
        self._lock = threading.Lock()

    def subscribe(self, event_type: EventType, callback: Subscriber) -> None:
        with self._lock:
            self._subscribers.setdefault(event_type, []).append(callback)

    def publish(self, event_type: EventType, data: Optional[Dict[str, Any]] = None) -> Event:
        event = Event(event_type=event_type, timestamp=time.time(), data=data or {})
        with self._lock:
            listeners = list(self._subscribers.get(event_type, []))
        for callback in listeners:
            callback(event)
        return event


# Module-level singleton
_bus: Optional[EventBus] = None
_bus_lock = threading.Lock()


def get_event_bus() -> EventBus:
    """Return the module-level EventBus singleton."""
    global _bus
    with _bus_lock:
        if _bus is None:
            _bus = EventBus()
        return _bus
