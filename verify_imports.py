#!/usr/bin/env python3
"""Verification script to test all imports and basic initialization."""

import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

print("=" * 60)
print("NOVA AI — Import Verification")
print("=" * 60)
print()

errors = []

# Test 1: Core imports
print("[1/8] Testing core imports...")
try:
    from core.config import get_config
    from core.types import Message, Role, ToolCall
    from core.registry import ToolRegistry, AgentRegistry, EngineRegistry
    from core.events import get_event_bus
    print("  ✓ Core imports OK")
except Exception as e:
    errors.append(f"Core imports: {e}")
    print(f"  ✗ Core imports FAILED: {e}")

# Test 2: Security
print("[2/8] Testing security module...")
try:
    from security import detect_injection, sanitize_input
    print("  ✓ Security module OK")
except Exception as e:
    errors.append(f"Security: {e}")
    print(f"  ✗ Security module FAILED: {e}")

# Test 3: Engine
print("[3/8] Testing engine...")
try:
    from engine.ollama import OllamaEngine
    print("  ✓ Engine OK")
except Exception as e:
    errors.append(f"Engine: {e}")
    print(f"  ✗ Engine FAILED: {e}")

# Test 4: Tools
print("[4/8] Testing tools...")
try:
    from tools.registry import tool_collection
    from tools.builtin import register_builtin_tools
    register_builtin_tools()
    n_tools = len(tool_collection.all())
    print(f"  ✓ Tools OK ({n_tools} tools registered)")
    if n_tools < 15:
        errors.append(f"Only {n_tools} tools registered (expected 15+)")
except Exception as e:
    errors.append(f"Tools: {e}")
    print(f"  ✗ Tools FAILED: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Agent
print("[5/8] Testing agent...")
try:
    from agents.native_react import NativeReActAgent
    print("  ✓ Agent module OK")
except Exception as e:
    errors.append(f"Agent: {e}")
    print(f"  ✗ Agent module FAILED: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Speech modules
print("[6/8] Testing speech modules...")
try:
    from speech.stt import STT
    from speech.tts import TTS
    from speech.vad import AudioCapture
    print("  ✓ Speech modules OK")
except Exception as e:
    errors.append(f"Speech: {e}")
    print(f"  ✗ Speech modules FAILED: {e}")

# Test 7: Sessions
print("[7/8] Testing sessions...")
try:
    from sessions import SessionStore
    print("  ✓ Sessions module OK")
except Exception as e:
    errors.append(f"Sessions: {e}")
    print(f"  ✗ Sessions module FAILED: {e}")

# Test 8: Intent router
print("[8/8] Testing intent router...")
try:
    from tools.intent_router import route_intent
    result = route_intent("turn up the volume")
    if "volume_control" in result:
        print(f"  ✓ Intent router OK (correctly routed to volume_control)")
    else:
        errors.append(f"Intent router returned wrong tool: {result}")
        print(f"  ✗ Intent router incorrect: expected volume_control, got {result}")
except Exception as e:
    errors.append(f"Intent router: {e}")
    print(f"  ✗ Intent router FAILED: {e}")

print()
print("=" * 60)
if errors:
    print(f"FAILED: {len(errors)} error(s)")
    for err in errors:
        print(f"  - {err}")
    sys.exit(1)
else:
    print("SUCCESS: All imports verified ✓")
    print("Ready to run main.py")
    sys.exit(0)
