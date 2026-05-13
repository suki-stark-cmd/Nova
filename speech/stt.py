"""Speech-to-Text using Faster-Whisper.

Reverse-engineered from OpenJarvis `speech/faster_whisper.py`.
Direct integration instead of registry-based backend for simplicity.
"""

from __future__ import annotations
import numpy as np
from core.config import get_config


class STT:
    """Local speech-to-text using Faster-Whisper (CTranslate2)."""

    def __init__(self):
        cfg = get_config()
        print(f"  Loading Whisper '{cfg.speech.stt_model}'...")
        from faster_whisper import WhisperModel
        self._model = WhisperModel(
            cfg.speech.stt_model,
            device=cfg.speech.stt_device,
            compute_type=cfg.speech.stt_compute_type,
        )
        self._language = cfg.speech.stt_language
        self._prompt = cfg.speech.stt_prompt
        print("  Whisper ready ✓")

    def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe audio numpy array to text."""
        segments, _ = self._model.transcribe(
            audio,
            beam_size=5,
            language=self._language,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
            condition_on_previous_text=False,
            initial_prompt=self._prompt,
        )
        return " ".join([seg.text.strip() for seg in segments]).strip()
