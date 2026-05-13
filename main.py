"""Nova AI — Main Entry Point.

Modular AI voice assistant reverse-engineered from OpenJarvis architecture.
Runs locally with llama3.2:1b via Ollama.

Architecture:
  ┌─────────┐    ┌─────┐    ┌───────────────┐    ┌───────┐
  │  Audio   │───▸│ STT │───▸│ Native ReAct  │───▸│  TTS  │
  │ Capture  │    │     │    │   Agent Loop   │    │       │
  └─────────┘    └─────┘    └───────┬───────┘    └───────┘
                                    │
                              ┌─────▼─────┐
                              │   Tools    │
                              │ Weather    │
                              │ Time       │
                              │ YouTube    │
                              │ Calculator │
                              │ Web Search │
                              │ System Cmd │
                              │ File R/W   │
                              │ Think      │
                              │ HTTP Req   │
                              └───────────┘

Subsystems (from OpenJarvis):
  - core/     → Registry, Types, Events, Config, Prompt Builder
  - engine/   → Ollama backend (native tool calling)
  - agents/   → NativeReActAgent (dual-mode: structured + text fallback)
  - tools/    → 10 built-in tools
  - speech/   → Faster-Whisper STT + Edge-TTS
  - sessions/ → SQLite-backed conversation persistence
  - scheduler/→ Background task scheduling (cron/interval/once)
  - security/ → Injection detection, file policy, command blocking
  - system/   → SystemBuilder (fluent builder pattern)
"""

import sys
import time
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.config import get_config
from security import detect_injection, sanitize_input
from speech.vad import AudioCapture
from speech.stt import STT
from speech.tts import TTS
from agents.native_react import NativeReActAgent


def main():
    cfg = get_config()

    print()
    print("═" * 60)
    print("  ███╗   ██╗ ██████╗ ██╗   ██╗ █████╗ ")
    print("  ████╗  ██║██╔═══██╗██║   ██║██╔══██╗")
    print("  ██╔██╗ ██║██║   ██║██║   ██║███████║")
    print("  ██║╚██╗██║██║   ██║╚██╗ ██╔╝██╔══██║")
    print("  ██║ ╚████║╚██████╔╝ ╚████╔╝ ██║  ██║")
    print("  ╚═╝  ╚═══╝ ╚═════╝   ╚═══╝  ╚═╝  ╚═╝")
    print()
    print("  OpenJarvis Architecture • Local AI Assistant")
    print("═" * 60)
    print(f"  Engine: {cfg.intelligence.preferred_engine}")
    print(f"  Model:  {cfg.intelligence.default_model}")
    print(f"  Speech: {cfg.speech.stt_model} (STT) • {cfg.speech.tts_voice} (TTS)")
    print("═" * 60)
    print()

    # ── Initialize Subsystems ─────────────────────────────────
    print("[1/5] Initializing audio capture...")
    try:
        audio = AudioCapture()
    except Exception as e:
        print(f"  ERROR: Audio capture failed: {e}")
        return

    print("[2/5] Loading speech-to-text...")
    try:
        stt = STT()
    except Exception as e:
        print(f"  ERROR: STT loading failed: {e}")
        return

    print("[3/5] Initializing text-to-speech...")
    try:
        tts = TTS()
    except Exception as e:
        print(f"  ERROR: TTS initialization failed: {e}")
        return

    print("[4/5] Starting agent...")
    try:
        agent = NativeReActAgent()
    except Exception as e:
        print(f"  ERROR: Agent initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Session persistence (from OpenJarvis sessions/)
    session_store = None
    session = None
    print("[5/5] Loading session store...")
    try:
        from sessions import SessionStore
        session_store = SessionStore()
        session = session_store.get_or_create("default")
        print(f"  Session: {session.session_id} ({len(session.messages)} messages)")
    except Exception as e:
        print(f"  Sessions disabled: {e}")

    if not session:
        session = None  # Ensure session is defined

    print()
    print("═" * 60)
    print("  NOVA is ready. Speak or type 'quit' to exit.")
    print(f"  Tools: {len(agent._all_tools)} | Security: ON")
    print("═" * 60)
    print()

    greeting = "Nova is ready. How can I help you?"
    print(f"NOVA: {greeting}")
    tts.speak(greeting, blocking=True)

    # ── Main Loop ─────────────────────────────────────────────
    while True:
        try:
            # Wait for TTS to finish before listening
            if tts.is_speaking:
                time.sleep(0.1)
                continue

            # 1. Listen (VAD)
            raw_audio = audio.record_utterance()
            if raw_audio is None:
                continue

            # 2. Transcribe (Whisper)
            user_text = stt.transcribe(raw_audio)
            if not user_text:
                continue
            print(f"\nYou: {user_text}")

            # System Exit
            if user_text.lower().strip() in ["stop", "quit", "exit", "shutdown", "bye"]:
                bye = "Shutting down. Goodbye!"
                print(f"NOVA: {bye}")
                tts.speak(bye, blocking=True)
                break

            # 3. Security checks (from OpenJarvis security/)
            user_text = sanitize_input(user_text)
            injection = detect_injection(user_text)
            if injection:
                print(f"  [Security] {injection}")
                response_text = "I detected a potentially unsafe request. Please rephrase."
                print(f"\nNOVA: {response_text}")
                tts.speak(response_text)
                continue

            # 4. Agent Execution (Native Tool-Calling Loop)
            print("NOVA is thinking...")
            response_text = agent.chat(user_text, tts_callback=tts.speak)

            # 5. Save to session (from OpenJarvis sessions/)
            if session_store and session:
                try:
                    session_store.save_message(session.session_id, "user", user_text)
                    if response_text:
                        session_store.save_message(session.session_id, "assistant", response_text)
                except Exception as e:
                    # Session save failed, but don't break the loop
                    pass

            # 6. Speak Response (Edge-TTS)
            if response_text:
                print(f"\nNOVA: {response_text}")
                tts.speak(response_text)

        except KeyboardInterrupt:
            print("\nShutting down by user interrupt...")
            break
        except Exception as e:
            print(f"\n[Error] {e}")
            import traceback
            traceback.print_exc()

    # Cleanup
    if session_store:
        session_store.close()


if __name__ == "__main__":
    main()
