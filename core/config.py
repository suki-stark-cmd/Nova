"""Configuration loader for Nova AI.

Reverse-engineered from OpenJarvis `core/config.py`.
Uses TOML config file instead of the massive 57KB config system.
"""

from __future__ import annotations
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Fallback
    except ImportError:
        tomllib = None


@dataclass
class IntelligenceConfig:
    default_model: str = "llama3.2:1b"
    preferred_engine: str = "ollama"
    temperature: float = 0.3
    max_tokens: int = 512
    num_ctx: int = 2048


@dataclass
class AgentConfig:
    default_agent: str = "native_react"
    max_turns: int = 5
    tools: str = "get_weather,get_time,play_youtube,calculator,web_search,system_command"
    system_prompt: str = (
        "You are NOVA, a smart AI voice assistant running locally. "
        "Keep answers brief and conversational since they are spoken aloud. "
        "Use tools when needed."
    )


@dataclass
class OllamaEngineConfig:
    host: str = "http://localhost:11434"
    timeout: float = 120.0


@dataclass
class EngineConfig:
    default: str = "ollama"
    ollama: OllamaEngineConfig = field(default_factory=OllamaEngineConfig)


@dataclass
class SpeechConfig:
    stt_backend: str = "faster-whisper"
    stt_model: str = "small"
    stt_device: str = "cpu"
    stt_compute_type: str = "int8"
    stt_language: str = "en"
    stt_prompt: str = "Nova, play Tamil songs on YouTube. What is the weather in Karur, Tamil Nadu?"
    tts_backend: str = "edge-tts"
    tts_voice: str = "en-US-GuyNeural"
    tts_rate: str = "+10%"


@dataclass
class AudioConfig:
    sample_rate: int = 16000
    channels: int = 1
    chunk_secs: float = 0.1
    vad_threshold: float = 0.025
    vad_confirm_chunks: int = 2
    silence_secs: float = 1.2
    max_record_secs: int = 30
    min_speech_secs: float = 0.5


@dataclass
class NovaConfig:
    """Top-level configuration object for Nova AI."""
    intelligence: IntelligenceConfig = field(default_factory=IntelligenceConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    engine: EngineConfig = field(default_factory=EngineConfig)
    speech: SpeechConfig = field(default_factory=SpeechConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)


def _apply_dict(obj: Any, data: Dict[str, Any]) -> None:
    """Apply a flat dict to a dataclass instance."""
    for key, value in data.items():
        if hasattr(obj, key) and not isinstance(value, dict):
            setattr(obj, key, value)


def load_config(path: Optional[Path] = None) -> NovaConfig:
    """Load configuration from a TOML file.

    Search order: explicit path → ./nova.toml → defaults
    """
    config = NovaConfig()

    if path is None:
        # Search in current dir, then script dir
        candidates = [
            Path("nova.toml"),
            Path(__file__).resolve().parent.parent / "nova.toml",
        ]
        for c in candidates:
            if c.exists():
                path = c
                break

    if path and path.exists() and tomllib is not None:
        with open(path, "rb") as f:
            data = tomllib.load(f)

        if "intelligence" in data:
            _apply_dict(config.intelligence, data["intelligence"])
        if "agent" in data:
            _apply_dict(config.agent, data["agent"])
        if "engine" in data:
            if "ollama" in data.get("engine", {}):
                _apply_dict(config.engine.ollama, data["engine"]["ollama"])
        if "speech" in data:
            _apply_dict(config.speech, data["speech"])
        if "audio" in data:
            _apply_dict(config.audio, data["audio"])

    # Environment setup
    os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

    return config


# Module-level cached config
_config: Optional[NovaConfig] = None


def get_config() -> NovaConfig:
    """Return the cached config singleton."""
    global _config
    if _config is None:
        _config = load_config()
    return _config
