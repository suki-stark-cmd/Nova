# NOVA Installation Guide

## System Requirements

### Minimum
- **OS:** Windows 10 or 11
- **CPU:** Any modern CPU (Intel/AMD/Apple Silicon via Parallels)
- **RAM:** 4GB (8GB+ recommended)
- **Disk:** 10GB free (for models and dependencies)
- **Audio:** Working microphone and speaker

### Recommended
- **CPU:** 4+ cores (better inference speed)
- **RAM:** 8-16GB
- **SSD:** Faster model loading
- **Audio:** High-quality mic for better STT accuracy

---

## Step-by-Step Installation

### 1. Install Ollama

Ollama is the LLM inference engine. It manages model downloads and inference.

**Download:**
- Go to [ollama.ai](https://ollama.ai)
- Download the Windows installer
- Run installer, follow prompts

**Verify Installation:**
```bash
ollama --version
```

**Start Ollama Server:**
```bash
ollama serve
```

This starts a local server on `http://localhost:11434`. Leave this terminal open.

**Download Model:**
In a new terminal:
```bash
ollama pull llama3.2:1b
```

This downloads the 1B parameter model (~2GB). First time takes 5-10 minutes.

---

### 2. Install Python 3.11+

**Option A: Official Python (Recommended)**
- Download from [python.org](https://www.python.org/downloads/)
- Run installer
- **Important:** Check "Add Python to PATH"
- Verify: `python --version` should show 3.11+

**Option B: Windows Store**
- Open Windows Store
- Search "Python 3.11" or higher
- Install

**Verify:**
```bash
python --version
pip --version
```

---

### 3. Clone Repository

```bash
# Navigate to desired location
cd D:\AI-ML

# Clone NOVA
git clone https://github.com/suki-stark-cmd/Nova.git
cd Nova
```

---

### 4. Create Virtual Environment (Optional but Recommended)

Using a virtual environment prevents conflicts with other Python projects.

```bash
# Create venv
python -m venv venv

# Activate venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

---

### 5. Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- **ollama** - Ollama client
- **faster-whisper** - Speech recognition
- **edge-tts** - Text-to-speech
- **pyttsx3** - Offline TTS fallback
- **sounddevice** - Audio capture
- **numpy** - Numerics
- **pygame** - Audio playback
- **ddgs** - Web search
- **tomli** - Config parsing

**Expected time:** 2-5 minutes

**Verify Installation:**
```bash
python verify_imports.py
```

Should output:
```
✓ Core module imports successful
✓ Security checks working
✓ Engine initialized
✓ Tools registered (24 total)
...
SUCCESS: All systems ready
```

---

## Configuration

### nova.toml Settings

Edit `nova.toml` to customize behavior:

```toml
[intelligence]
default_model = "llama3.2:1b"      # Model to use
temperature = 0.3                   # Lower = more deterministic
max_tokens = 512                    # Max response length
num_ctx = 2048                      # Context window

[agent]
max_turns = 5                       # Max ReAct iterations
tools = "volume_control,brightness_control,..."

[engine.ollama]
host = "http://localhost:11434"     # Ollama server
timeout = 120                       # Inference timeout (seconds)

[speech]
stt_backend = "faster-whisper"
stt_model = "small"                 # small/medium/large
tts_backend = "edge-tts"
voice = "en-US-GuyNeural"           # Or other voices
rate = "1.0"                        # Speech rate

[audio]
vad_threshold = 0.02                # Silence sensitivity
silence_secs = 1.5                  # Silence confirmation
```

---

## Running NOVA

### Prerequisites Check
1. **Ollama Server Running**
   - Terminal 1: `ollama serve`
2. **Model Downloaded**
   - `ollama pull llama3.2:1b`
3. **Python Dependencies Installed**
   - `pip install -r requirements.txt`

### Start NOVA

In a new terminal:
```bash
python main.py
```

Expected output:
```
════════════════════════════════════════════════════════════
  ███╗   ██╗ ██████╗ ██╗   ██╗ █████╗ 
  ████╗  ██║██╔═══██╗██║   ██║██╔══██╗
  ██╔██╗ ██║██║   ██║██║   ██║███████║
  ██║╚██╗██║██║   ██║╚██╗ ██╔╝██╔══██║
  ██║ ╚████║╚██████╔╝ ╚████╔╝ ██║  ██║
  ╚═╝  ╚═══╝ ╚═════╝   ╚═══╝  ╚═╝  ╚═╝

  OpenJarvis Architecture • Local AI Assistant
════════════════════════════════════════════════════════════

[1/5] Initializing audio capture...
[2/5] Loading speech-to-text...
[3/5] Initializing text-to-speech...
[4/5] Starting agent...
[5/5] Loading session store...

════════════════════════════════════════════════════════════
  NOVA is ready. Speak or type 'quit' to exit.
  Tools: 24 | Security: ON
════════════════════════════════════════════════════════════

NOVA: Nova is ready. How can I help you?
```

---

## First Time Setup

### 1. Microphone Test
```
You: Test microphone
NOVA should respond with acknowledgment
```

### 2. Try Simple Command
```
You: What time is it?
NOVA: [Tool] get_time({...})
NOVA: It's [current time].
```

### 3. Try Tool Command
```
You: Set volume to 50 percent
NOVA: [Tool] volume_control({"action": "set", "level": "50"})
NOVA: Volume set to 50%.
```

### 4. Exit
```
You: quit
NOVA terminates gracefully
```

---

## Troubleshooting Installation

### "Python not found"
```bash
# Verify Python installation
python --version

# If not found, add to PATH:
# Go to System Properties → Environment Variables → PATH
# Add Python installation directory (e.g., C:\Python311)
```

### "pip install fails"
```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Then try again
pip install -r requirements.txt

# If specific package fails:
pip install --upgrade setuptools wheel
```

### "Ollama connection refused"
```bash
# Make sure Ollama is running:
ollama serve

# If it crashes, check:
ollama list    # List installed models
ollama status  # Check service status

# Restart:
taskkill /IM ollama.exe
ollama serve
```

### "Model not found"
```bash
ollama list
# If llama3.2:1b not listed:
ollama pull llama3.2:1b
```

### "No audio input detected"
```bash
# Check audio devices:
python -c "import sounddevice; print(sounddevice.query_devices())"

# Test recording:
python -c "from speech.vad import AudioCapture; a = AudioCapture(); print(a.record_utterance())"
```

### "Whisper model not loading"
```bash
# Force reinstall:
pip install --upgrade faster-whisper

# Clear cache:
rm -rf ~/.cache/huggingface

# Try again
```

### "Memory error / OOM"
- Reduce max_tokens in nova.toml (try 256)
- Close other applications
- Restart Ollama: `ollama serve`
- Consider upgrading RAM if persistent

### "STT quality is poor"
- Check microphone is working: `sounddevice` test above
- Try medium model instead of small: `nova.toml` → `stt_model = "medium"`
- Ensure quiet environment for recording

### "TTS has weird voice"
- Different voice: `nova.toml` → `voice = "en-US-AriaNeural"` (etc.)
- List all voices: Check [Edge-TTS documentation](https://github.com/rany2/edge-tts/wiki/List-of-Supported-Voices)

---

## Running from Text (No Voice)

If you want to use text input instead of voice:

```python
# In main.py, replace:
# agent.chat(transcript)
# With:
import sys
while True:
    user_input = input("You: ")
    if user_input.lower() in ("quit", "exit", "stop"):
        break
    response = agent.chat(user_input)
    print(f"NOVA: {response}")
```

---

## Advanced Configuration

### Using Larger Model
```bash
# Download larger model
ollama pull llama3.2:7b

# Update nova.toml:
[intelligence]
default_model = "llama3.2:7b"
```

Better quality but slower (needs 16GB+ RAM).

### Using Different STT Model
```toml
[speech]
stt_model = "medium"    # more accurate, slower
# or
stt_model = "large"     # most accurate, slowest
```

### Multiple Voices
Different voice for different responses:
```python
# In agent code:
if "weather" in query:
    tts.speak(response, voice="en-US-AriaNeural")
else:
    tts.speak(response)  # Use default
```

---

## Updating NOVA

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Verify
python verify_imports.py
```

---

## Uninstalling

```bash
# Remove virtual environment (if used)
rmdir /s venv

# Uninstall Python packages
pip uninstall -r requirements.txt -y

# Delete repository
rmdir /s Nova

# Uninstall Ollama
# Use Windows "Add/Remove Programs" or:
# Download Ollama uninstaller from ollama.ai
```

---

## Getting Help

- **Errors:** Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Issues:** [GitHub Issues](https://github.com/suki-stark-cmd/Nova/issues)
- **Discussions:** [GitHub Discussions](https://github.com/suki-stark-cmd/Nova/discussions)

---

**Last Updated:** May 13, 2026
