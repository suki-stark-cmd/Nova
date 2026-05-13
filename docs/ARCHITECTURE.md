# NOVA Architecture

## System Overview

NOVA is a production-grade voice assistant built on a modern layered architecture designed specifically for small language models (1B parameters) running on laptops.

```
┌─────────────────────────────────────────────────────────┐
│                   User Voice Input                       │
└────────────────┬────────────────────────────────────────┘
                 │
         ┌───────▼────────┐
         │  VAD + Audio   │  (speech/vad.py)
         │  Capture       │  • Energy-based detection
         └───────┬────────┘  • Silence confirmation
                 │
         ┌───────▼────────┐
         │  Speech-to-    │  (speech/stt.py)
         │  Text (STT)    │  • Faster-Whisper (small)
         │                │  • int8 quantized
         └───────┬────────┘  • CPU inference
                 │
         ┌───────▼────────┐
         │  Query Text    │
         │  (user input)  │
         └───────┬────────┘
                 │
         ┌───────▼──────────────┐
         │  Intent Router       │  (tools/intent_router.py)
         │  Select 5-6 tools    │  • Keyword matching
         │  from 24 available   │  • Tool exclusion rules
         └───────┬──────────────┘  • Context-aware
                 │
         ┌───────▼──────────────┐
         │  Message Building    │  (core/prompt_builder.py)
         │  • System prompt     │  • Persona injection
         │  • Conversation hist │  • Tool schemas
         │  • Tool definitions  │  • Context window mgmt
         └───────┬──────────────┘
                 │
         ┌───────▼──────────────┐
         │  Ollama LLM          │  (engine/ollama.py)
         │  llama3.2:1b         │  • Native tool-calling
         │  ReAct Loop          │  • Token streaming
         │  (up to 5 turns)     │  • Error recovery
         └───────┬──────────────┘
                 │
    ┌────────────┼────────────┐
    │                         │
    ▼                         ▼
┌───────────┐         ┌──────────────┐
│ Tool Call │         │  Direct Text │
│ Struct    │         │  Response    │
└─────┬─────┘         └──────┬───────┘
      │                      │
      └──────────┬───────────┘
                 │
         ┌───────▼──────────────┐
         │  Tool Executor       │  (tools/base.py)
         │  • Timeout mgmt      │  • Result formatting
         │  • Error handling    │  • Event emission
         │  • Security checks   │  • 24 registered tools
         └───────┬──────────────┘
                 │
         ┌───────▼──────────────┐
         │  Tool Results        │
         │  (structured output) │
         └───────┬──────────────┘
                 │
         ┌───────▼──────────────┐
         │  Response Cleaner    │  (agents/native_react.py)
         │  • Remove JSON       │  • Strip meta-commentary
         │  • Fix formatting    │  • One sentence only
         └───────┬──────────────┘
                 │
         ┌───────▼────────┐
         │  Text-to-      │  (speech/tts.py)
         │  Speech (TTS)  │  • Edge-TTS primary
         │                │  • pyttsx3 fallback
         └───────┬────────┘  • Async playback
                 │
         ┌───────▼────────┐
         │  Audio Output  │  pygame
         │  (speaker)     │  (speaker playback)
         └────────────────┘
```

---

## Core Components

### 1. Core Framework (`core/`)

#### `config.py` - Configuration Management
- **Purpose:** Load and validate `nova.toml` settings
- **Classes:** IntelligenceConfig, AgentConfig, OllamaEngineConfig, SpeechConfig, AudioConfig, NovaConfig
- **Features:** 
  - TOML parsing with schema validation
  - Environment override support
  - Type-safe configuration access

#### `types.py` - Canonical Data Types
- **Purpose:** Shared data structures across all components
- **Classes:** 
  - `Role` (USER, ASSISTANT, SYSTEM)
  - `Message` (role, content, tool_calls)
  - `ToolCall` (id, name, arguments)
  - `ToolResult` (tool_name, content, success, execution_time)
  - `ToolSpec` (name, description, parameters, timeout)
  - `AgentResult` (content, tool_results, turns)
  - `Conversation` (list of messages with metadata)

#### `registry.py` - Plugin System
- **Purpose:** Runtime discovery of engines, agents, tools, and speech backends
- **Pattern:** Decorator-based registration
- **Classes:** RegistryBase, EngineRegistry, AgentRegistry, ToolRegistry, SpeechRegistry
- **Key:** Allows graceful overwrite of duplicate registrations

#### `events.py` - Event Bus
- **Purpose:** Thread-safe pub/sub for inter-component communication
- **Events:**
  - INFERENCE_START/END
  - TOOL_CALL_START/END
  - AGENT_TURN_START/END
- **Pattern:** Singleton EventBus with context-aware callbacks

#### `prompt_builder.py` - System Prompt Assembly
- **Purpose:** Dynamically construct system prompts with persona/memory injection
- **Classes:** SystemPromptBuilder
- **Features:**
  - Soul/personality injection
  - Memory system integration
  - User context files
  - Tool schema injection
  - Frozen prefix for consistency

---

### 2. Inference Engine (`engine/`)

#### `base.py` - Abstract Engine
- **Purpose:** Define common interface for LLM backends
- **ABC Methods:** generate(), list_models(), health()
- **Interface:** Engine agnostic design

#### `ollama.py` - Ollama Backend
- **Purpose:** Communicate with local Ollama server
- **Implementation:**
  - Native tool-calling API support
  - Token streaming with callbacks
  - Error recovery and retry logic
  - Connection pooling
- **Returns:** {content, tool_calls, usage, model, message}

---

### 3. Agent (`agents/`)

#### `base.py` - Base Agent
- **Purpose:** Abstract base class for all agents
- **Methods:**
  - _emit_turn_start/end (event bus integration)
  - _build_messages (conversation assembly)
  - _generate (delegate to engine)
  - run() (abstract - to be implemented)

#### `native_react.py` - ReAct Agent (Main)
- **Purpose:** Reason-Act loop for tool-based problem solving
- **Algorithm:**
  1. Build message history with tool schemas
  2. Call Ollama for next action
  3. Parse tool calls (dual mode: structured + text fallback)
  4. Execute tools with timeout and error handling
  5. Add tool results to context
  6. Repeat until final answer (max 5 turns)
  7. Clean response and return
- **Dual-Mode Tool Calling:**
  - Structured: Parse Ollama's native tool_calls array
  - Text Fallback: Extract JSON from content for small models
- **Response Cleaning:**
  - Strip JSON artifacts
  - Remove meta-commentary
  - Enforce one-sentence responses
  - Capitalize properly

---

### 4. Tools System (`tools/`)

#### `base.py` - Tool Foundation
- **Purpose:** Base class and executor for all tools
- **Classes:**
  - BaseTool (ABC)
    - spec property (returns ToolSpec)
    - execute(**params) (abstract)
    - to_ollama_tool() (converts to Ollama schema)
  - ToolExecutor
    - execute(tool_call) dispatcher
    - Timeout management (default 30s)
    - Event emission (START/END)
    - Error handling and logging

#### `registry.py` - Tool Collection
- **Purpose:** Centralized tool registry
- **Classes:** ToolCollection (singleton: tool_collection)
- **Methods:** add(), get(), all(), names(), clear()
- **Safety:** Prevents duplicate registration

#### `builtin.py` - Generic Tools (9 tools)
- WeatherTool (wttr.in API)
- TimeTool (local time/date)
- YouTubeTool (DEPRECATED, kept for compatibility)
- CalculatorTool (AST-safe math)
- WebSearchTool (ddgs library)
- SystemCommandTool (subprocess with filtering)
- FileReadTool (with size/path limits)
- FileWriteTool (with security checks)
- ThinkTool (reasoning scratchpad)
- HttpRequestTool (GET/POST requests)

#### `windows_control.py` - Windows Tools (8 tools)
- VolumeControlTool
- BrightnessControlTool
- AppLauncherTool
- ScreenshotTool
- LockScreenTool
- WifiToggleTool
- SystemInfoTool
- WindowManageTool

#### `media_control.py` - Media Tools (7 tools)
- MediaPlaybackTool
- AppleMusicTool
- EdgeBrowserTool
- YouTubeEdgeTool
- AppleNotesTool
- AppleRemindersTool
- AlarmTimerTool

#### `intent_router.py` - Intent Routing
- **Purpose:** Map user queries to relevant tools
- **Algorithm:**
  1. Match keywords against 60+ keyword patterns
  2. Score tools by match count
  3. Sort by relevance
  4. Apply exclusion rules (e.g., media_control excludes web_search)
  5. Return top 8 tools with always-on (time, weather, calculator, think)
- **Result:** 5-6 relevant tools instead of all 24, dramatically improving small model performance

---

### 5. Speech Processing (`speech/`)

#### `vad.py` - Voice Activity Detection
- **Purpose:** Listen for user speech automatically
- **Implementation:**
  - Energy-based RMS threshold detection
  - Configurable sensitivity (default 0.02)
  - Silence confirmation (default 1.5s)
  - Real-time audio capture via sounddevice
- **Class:** AudioCapture
- **Method:** record_utterance() → numpy array or None

#### `stt.py` - Speech-to-Text
- **Purpose:** Convert audio to text
- **Implementation:**
  - Faster-Whisper (small model, int8 quantized)
  - CPU-based inference (~1-2s for 10s audio)
  - No GPU required
- **Class:** STT
- **Method:** transcribe(audio) → str

#### `tts.py` - Text-to-Speech
- **Purpose:** Convert text to audio
- **Implementation:**
  - Primary: Edge-TTS (online, high quality)
  - Fallback: pyttsx3 (offline, lower quality)
  - Async speech synthesis
  - pygame-based playback
- **Classes:** TTS
- **Methods:**
  - speak(text, blocking) - async or blocking
  - _try_edge_tts(text) - tries online first
  - _use_pyttsx3_speak(text) - fallback offline

---

### 6. Session Management (`sessions/`)

#### `__init__.py` - SQLite Session Store
- **Purpose:** Persist conversation history
- **Storage:** ~/.nova/sessions.db
- **Classes:**
  - SessionMessage (role, content, timestamp)
  - Session (id, user_id, messages, metadata)
  - SessionStore (CRUD operations)
- **Features:**
  - Auto-cleanup of sessions >24h old
  - Message consolidation when context exceeds limit
  - Conversation history retrieval
  - Session consolidation algorithm

#### `compression.py` - Context Compression
- **Purpose:** Compress old messages to fit 2048-token context
- **Algorithms:**
  - SessionConsolidation (summarize oldest N%)
  - RuleBasedPrecompression (strip boilerplate)
  - TieredSummaries (L0→L1→L2 progressive compression)
- **Classes:** BaseCompressor, each algorithm extends it

---

### 7. Security (`security/`)

#### `__init__.py` - Security Guardrails
- **Purpose:** Multi-layer security checks
- **Functions:**
  - is_dangerous_command(cmd) - blocks rm -rf, format, etc.
  - is_sensitive_file(path) - blocks .env, SSH keys, etc.
  - detect_injection(text) - regex-based injection detection
  - sanitize_input(text) - removes control chars, limits length
- **Blocked Patterns:**
  - Commands: `rm -rf`, `del /s`, `format`, `shutdown`, fork bombs
  - Files: `.env`, `*_rsa`, `.pem`, `.key`, `credentials.json`, `.aws/*`
  - Injections: "system:", "admin:", "ignore previous instructions"

---

## Data Flow

### Conversation Cycle

```
1. USER SPEAKS
   AudioCapture.record_utterance() 
   → numpy array (audio samples)

2. SPEECH-TO-TEXT
   STT.transcribe(audio)
   → "Set the volume to 50"

3. SECURITY CHECK
   detect_injection() → False (safe)
   is_dangerous_command() → False (safe)

4. INTENT ROUTING
   route_intent(query)
   → [volume_control, open_app, system_info, ...]

5. MESSAGE BUILDING
   SystemPromptBuilder.build()
   → System prompt with persona + tools
   
   Build conversation messages:
   [system_prompt, ...history..., current_query]

6. LLM INFERENCE
   OllamaEngine.generate(messages, tools)
   → {content, tool_calls, usage, ...}

7. TOOL EXECUTION
   For each tool_call:
     ToolExecutor.execute(tool_call)
     → Tool runs with timeout
     → Result or error
   
   Add results to context
   If tool_calls present: loop to step 6
   Else: return content

8. RESPONSE CLEANING
   _clean_response(content)
   → Remove JSON, meta-commentary
   → One sentence
   → Natural language

9. SESSION SAVE
   SessionStore.save_message(user_input)
   SessionStore.save_message(response)

10. TEXT-TO-SPEECH
    TTS.speak(response)
    → Edge-TTS or pyttsx3
    → Audio playback via pygame
    → "Volume set to 50 percent"
```

---

## Performance Characteristics

| Component | Time | Notes |
|-----------|------|-------|
| VAD Listen | 0.1s | Continuous in background |
| Audio Capture | Variable | User speech duration |
| STT (Whisper small) | 1-2s | Per 10 seconds audio |
| Intent Routing | <50ms | Keyword matching |
| Message Building | 100-200ms | Context assembly |
| LLM Inference | 2-3s | llama3.2:1b on CPU |
| Tool Execution | 0.5-2s | Depends on tool |
| TTS (Edge) | 1s | Per 20 words |
| TTS (pyttsx3) | 0.5s | Faster but lower quality |
| **Total E2E** | **5-7s** | Typical command cycle |

---

## Context Window Management

- **Model Context:** 2048 tokens (llama3.2:1b limit)
- **Distribution:**
  - System prompt: ~300 tokens
  - Tool schemas: ~600 tokens
  - Conversation history: ~800 tokens
  - Current query + buffer: ~350 tokens
- **Compression Strategy:**
  1. Keep last 5 exchanges (10 messages)
  2. When limit exceeded: summarize oldest 30%
  3. Use tiered summaries (L0→L1→L2) for older messages
  4. Drop messages >24h old

---

## Error Handling & Recovery

| Error | Detection | Recovery |
|-------|-----------|----------|
| Ollama not running | Connection refused | Graceful error message |
| Microphone unavailable | Audio device error | Skip VAD, use text input |
| Whisper download fails | Import error | Fallback to text input |
| Edge-TTS DNS fails | Socket error | Fall back to pyttsx3 |
| Tool timeout | 30s threshold | Return timeout error |
| Tool crash | Exception catch | Continue to next tool |
| Invalid JSON from model | Parse error | Try text-based fallback |
| OOM during inference | Memory error | Clear cache, retry |

---

## Thread Safety

- **Event Bus:** Thread-safe with locks
- **Session Store:** SQLite provides atomic access
- **Audio Capture:** Runs in main thread (sound device is not thread-safe)
- **TTS:** Async operations with threading
- **Tool Executor:** Sequential execution in main thread

---

## Future Optimizations

1. **GPU Acceleration** - Support for NVIDIA/AMD GPU inference
2. **Quantization** - 4-bit/8-bit model loading
3. **Model Swapping** - Load different models for different tasks
4. **Parallel Tool Execution** - Run independent tools simultaneously
5. **Advanced Caching** - Cache tool results for repeated queries
6. **Multi-language** - Support non-English language packs

---

**Last Updated:** May 13, 2026  
**Version:** 1.0.0
