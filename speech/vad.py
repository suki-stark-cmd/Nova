"""Voice Activity Detection and Audio Capture.

Config-driven audio recording with energy-based VAD.
"""

from __future__ import annotations
import numpy as np
import sounddevice as sd
from core.config import get_config


class AudioCapture:
    """Energy-based VAD with config-driven parameters."""

    def __init__(self):
        self._cfg = get_config()

    @staticmethod
    def _rms(chunk: np.ndarray) -> float:
        return float(np.sqrt(np.mean(chunk ** 2)))

    def record_utterance(self) -> np.ndarray | None:
        """Record audio until silence is detected after speech."""
        cfg = self._cfg.audio
        sr = cfg.sample_rate
        chunk_n = int(sr * cfg.chunk_secs)
        max_ch = int(cfg.max_record_secs / cfg.chunk_secs)
        sil_max = int(cfg.silence_secs / cfg.chunk_secs)

        chunks = []
        pending = []
        sil_count = 0
        loud_streak = 0
        started = False

        print("\r🎤 Listening...  ", end="", flush=True)

        try:
            with sd.InputStream(samplerate=sr, channels=cfg.channels, dtype="float32") as stream:
                for _ in range(max_ch):
                    raw, _ = stream.read(chunk_n)
                    mono = raw[:, 0]
                    rms = self._rms(mono)

                    if rms > cfg.vad_threshold:
                        loud_streak += 1
                        pending.append(mono)
                        if not started and loud_streak >= cfg.vad_confirm_chunks:
                            print("\r● Recording...  ", end="", flush=True)
                            started = True
                            chunks = list(pending)
                            sil_count = 0
                        elif started:
                            chunks.append(mono)
                            sil_count = 0
                    else:
                        loud_streak = 0
                        if not started:
                            pending.append(mono)
                            if len(pending) > int(1.0 / cfg.chunk_secs):
                                pending.pop(0)
                        else:
                            chunks.append(mono)
                            sil_count += 1
                            if sil_count >= sil_max:
                                break
        except Exception as e:
            print(f"Mic error: {e}")
            return None

        print("\r                 \r", end="", flush=True)
        if not chunks:
            return None
        audio = np.concatenate(chunks).astype(np.float32)
        if len(audio) < sr * cfg.min_speech_secs:
            return None
        return audio
