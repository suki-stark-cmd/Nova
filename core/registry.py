"""Decorator-based registry for runtime discovery of pluggable components.

Reverse-engineered from OpenJarvis `core/registry.py`.
Each typed subclass gets its own isolated storage so registrations
in one registry never leak into another.
"""

from __future__ import annotations
from typing import Any, Callable, Dict, Generic, Tuple, TypeVar

T = TypeVar("T")


class RegistryBase(Generic[T]):
    """Generic registry base class with class-specific entry isolation."""

    @classmethod
    def _entries(cls) -> Dict[str, T]:
        attr_name = f"_registry_entries_{cls.__name__}"
        storage = getattr(cls, attr_name, None)
        if storage is None:
            storage: Dict[str, T] = {}
            setattr(cls, attr_name, storage)
        return storage

    @classmethod
    def register(cls, key: str) -> Callable[[T], T]:
        """Decorator that registers *entry* under *key*."""
        def decorator(entry: T) -> T:
            entries = cls._entries()
            if key in entries:
                import warnings
                warnings.warn(f"{cls.__name__} already has entry for '{key}', overwriting")
            entries[key] = entry
            return entry
        return decorator

    @classmethod
    def get(cls, key: str) -> T:
        """Retrieve entry for *key*, raises KeyError if missing."""
        try:
            return cls._entries()[key]
        except KeyError as exc:
            raise KeyError(f"{cls.__name__} has no entry for '{key}'") from exc

    @classmethod
    def keys(cls) -> Tuple[str, ...]:
        """Return all registered keys."""
        return tuple(cls._entries().keys())

    @classmethod
    def contains(cls, key: str) -> bool:
        """Check whether *key* is registered."""
        return key in cls._entries()

    @classmethod
    def create(cls, key: str, *args: Any, **kwargs: Any) -> Any:
        """Instantiate the entry for *key*."""
        entry = cls.get(key)
        return entry(*args, **kwargs)


# ── Typed Registries ──────────────────────────────────────────

class EngineRegistry(RegistryBase):
    """Registry for inference engine backends."""

class AgentRegistry(RegistryBase):
    """Registry for agent implementations."""

class ToolRegistry(RegistryBase):
    """Registry for tool implementations."""

class SpeechRegistry(RegistryBase):
    """Registry for speech backends."""
