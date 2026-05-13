"""Text-to-Speech using Edge-TTS with pyttsx3 fallback.

Tries Edge-TTS first (online), falls back to pyttsx3 (offline) on failure.
"""

from __future__ import annotations
import os
import re
import time
import threading
import tempfile
import asyncio
import logging
from core.config import get_config

logger = logging.getLogger(__name__)


class TTS:
    """Hybrid TTS with Edge-TTS (online) + pyttsx3 fallback (offline)."""

    def __init__(self):
        cfg = get_config()
        self._voice = cfg.speech.tts_voice
        self._rate = cfg.speech.tts_rate
        self._speaking = False
        self._use_pyttsx3 = False
        
        # Try to init pygame for Edge-TTS playback
        try:
            import pygame
            pygame.mixer.init()
            self._pygame_available = True
        except Exception as e:
            logger.warning(f"Pygame not available: {e}")
            self._pygame_available = False
        
        # Try to init pyttsx3 as fallback
        try:
            import pyttsx3
            self._pyttsx3_engine = pyttsx3.init()
            self._pyttsx3_engine.setProperty('rate', 150)  # Faster speech
            self._pyttsx3_available = True
            logger.info("pyttsx3 ready for offline TTS fallback")
        except Exception as e:
            logger.warning(f"pyttsx3 not available: {e}")
            self._pyttsx3_available = False
            self._pyttsx3_engine = None

    def speak(self, text: str, blocking: bool = False):
        """Speak text using Edge-TTS or pyttsx3 fallback. Non-blocking by default."""
        if not text:
            return
        
        # Strip markdown formatting
        text = re.sub(r"[*_`#\[\]()]", "", text).strip()

        # Try Edge-TTS first if pygame available
        if self._pygame_available:
            t = threading.Thread(target=self._try_edge_tts, args=(text,), daemon=True)
            t.start()
            if blocking:
                t.join()
        else:
            # Use fallback immediately
            self._use_pyttsx3_speak(text)
            if not blocking:
                return
            time.sleep(len(text) / 100)  # Rough estimate

    def _try_edge_tts(self, text: str):
        """Try Edge-TTS, fallback to pyttsx3 on failure."""
        self._speaking = True
        try:
            asyncio.run(self._edge_speak(text))
        except Exception as e:
            logger.warning(f"Edge-TTS failed ({type(e).__name__}), using pyttsx3 fallback")
            self._use_pyttsx3_speak(text)
        finally:
            self._speaking = False

    async def _edge_speak(self, text: str):
        import edge_tts
        communicate = edge_tts.Communicate(text, voice=self._voice, rate=self._rate)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tmp = f.name
        try:
            await communicate.save(tmp)
            import pygame
            pygame.mixer.music.load(tmp)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.05)
        finally:
            time.sleep(0.1)
            try:
                os.unlink(tmp)
            except OSError:
                pass

    def _use_pyttsx3_speak(self, text: str):
        """Fallback: Use pyttsx3 for offline speech synthesis."""
        if not self._pyttsx3_available or not self._pyttsx3_engine:
            logger.warning("No TTS backend available")
            return
        try:
            self._pyttsx3_engine.say(text)
            self._pyttsx3_engine.runAndWait()
        except Exception as e:
            logger.error(f"pyttsx3 error: {e}")

    @property
    def is_speaking(self) -> bool:
        return self._speaking
