# NOVA Troubleshooting Guide

Solutions to common issues and problems.

---

## Startup Issues

### "Ollama connection refused"

**Symptoms:**
- Error: `Connection refused` or `Cannot connect to localhost:11434`
- NOVA crashes on startup

**Solutions:**
1. **Start Ollama**
   ```bash
   ollama serve
   ```
   Leave this running in a separate terminal.

2. **Check if Ollama is installed**
   ```bash
   ollama --version
   ```
   If not found, download from [ollama.ai](https://ollama.ai)

3. **Check if port 11434 is in use**
   ```bash
   netstat -ano | findstr :11434
   ```
   If another service is using it, free the port or configure a different port in `nova.toml`

4. **Restart Ollama**
   ```bash
   taskkill /IM ollama.exe
   ollama serve
   ```

---

### "Model not found: llama3.2:1b"

**Symptoms:**
- Error: `model not found`
- Ollama is running but model missing

**Solutions:**
1. **Download the model**
   ```bash
   ollama pull llama3.2:1b
   ```
   First time downloads ~2GB (takes 5-10 minutes)

2. **Verify model is installed**
   ```bash
   ollama list
   ```
   Should show `llama3.2:1b`

3. **Use different model**
   ```bash
   ollama pull llama2
   # Update nova.toml:
   [intelligence]
   default_model = "llama2"
   ```

---

### "Python not found"

**Symptoms:**
- Error: `python: command not found`
- `pip` command doesn't work

**Solutions:**
1. **Verify Python installation**
   ```bash
   python --version
   python3 --version
   ```

2. **Install Python** (if needed)
   - Download from [python.org](https://www.python.org/downloads/)
   - Run installer
   - **IMPORTANT:** Check "Add Python to PATH"

3. **Add Python to PATH**
   - Go to System Properties → Environment Variables
   - Edit PATH variable
   - Add Python installation directory (e.g., `C:\Python311`)
   - Restart terminal/IDE

4. **Use full path**
   ```bash
   C:\Python311\python.exe main.py
   ```

---

### "Pip dependencies failed to install"

**Symptoms:**
- Error during `pip install -r requirements.txt`
- `ModuleNotFoundError` after installation

**Solutions:**
1. **Upgrade pip**
   ```bash
   python -m pip install --upgrade pip
   ```

2. **Clear pip cache**
   ```bash
   pip cache purge
   ```

3. **Install with verbose output**
   ```bash
   pip install -r requirements.txt -v
   ```

4. **Install specific packages**
   ```bash
   pip install ollama faster-whisper edge-tts
   # Check which one fails
   ```

5. **Check Python version**
   ```bash
   python --version  # Must be 3.11+
   ```

---

## Audio & Speech Issues

### "No audio input detected"

**Symptoms:**
- VAD not detecting voice
- NOVA isn't listening
- "Please speak..." prompt appears indefinitely

**Solutions:**
1. **Check microphone**
   ```bash
   # List audio devices
   python -c "import sounddevice; import pprint; pprint.pprint(sounddevice.query_devices())"
   ```

2. **Test microphone in Windows**
   - Settings → Privacy → Microphone → Test
   - Speak into microphone

3. **Restart audio device**
   - Unplug/replug microphone
   - Restart NOVA

4. **Adjust VAD sensitivity**
   Edit `nova.toml`:
   ```toml
   [audio]
   vad_threshold = 0.01    # Lower = more sensitive
   silence_secs = 2.0      # Wait longer for voice end
   ```

5. **Use different microphone**
   ```bash
   # In nova.toml, add device selection (advanced)
   # Check sounddevice output for device ID
   ```

---

### "STT quality is very poor"

**Symptoms:**
- Speech-to-text makes many mistakes
- "Whisper not hearing correctly"

**Solutions:**
1. **Use larger STT model**
   Edit `nova.toml`:
   ```toml
   [speech]
   stt_model = "medium"    # Instead of "small"
   ```
   Takes longer but more accurate. First run downloads ~700MB.

2. **Improve microphone quality**
   - Use external USB microphone (better than laptop mic)
   - Keep microphone clean
   - Position it properly (6-12 inches away)

3. **Reduce background noise**
   - Close other applications
   - Minimize browser tabs
   - Turn off background music/TV
   - Find quieter room

4. **Speak more clearly**
   - Don't rush words
   - Use normal volume
   - Pause between sentences

5. **Reinstall Whisper**
   ```bash
   pip install --upgrade faster-whisper
   ```

---

### "TTS has robotic/poor quality voice"

**Symptoms:**
- Text-to-speech sounds unnatural
- Strange pronunciation

**Solutions:**
1. **Change voice**
   Edit `nova.toml`:
   ```toml
   [speech]
   voice = "en-US-AriaNeural"  # Different voice
   ```
   Available voices: Check [Edge-TTS voices](https://github.com/rany2/edge-tts/wiki/List-of-Supported-Voices)

2. **Adjust speech rate**
   ```toml
   [speech]
   rate = "1.2"  # Slower (0.5-2.0)
   ```

3. **Check internet connection** (for Edge-TTS)
   If offline, should use pyttsx3 fallback automatically.

---

### "TTS fails with DNS error"

**Symptoms:**
- Error: `Cannot connect to host speech.platform.bing.com`
- No sound output

**Solutions:**
1. **Check internet connection**
   ```bash
   ping google.com
   ```

2. **Edge-TTS should fallback to pyttsx3**
   This should happen automatically. If not:
   ```bash
   # Reinstall pyttsx3
   pip install pyttsx3
   ```

3. **Verify pyttsx3 works offline**
   ```python
   import pyttsx3
   engine = pyttsx3.init()
   engine.say("Hello world")
   engine.runAndWait()
   ```

4. **Check Windows text-to-speech**
   - Settings → Easy of access → Speech
   - Verify TTS engine available

---

## Performance Issues

### "NOVA is very slow"

**Symptoms:**
- Takes 10+ seconds per command
- Long inference time
- System is sluggish

**Solutions:**
1. **Close background applications**
   - Reduces RAM usage
   - Frees CPU for Ollama

2. **Reduce model size temporarily**
   See if it helps (temporary workaround)

3. **Check system resources**
   ```bash
   # Windows Task Manager
   # Check CPU/RAM/Disk usage
   ```

4. **Reduce max_tokens**
   Edit `nova.toml`:
   ```toml
   [intelligence]
   max_tokens = 256  # Shorter responses = faster
   ```

5. **Check Ollama status**
   ```bash
   ollama status
   ```
   Restart if needed: `taskkill /IM ollama.exe`

6. **Use faster hardware**
   - Upgrade RAM (CPU-bound, benefits from more cache)
   - Use SSD instead of HDD
   - Close other compute-intensive tasks

---

### "Out of Memory (OOM) error"

**Symptoms:**
- Error: `MemoryError` or `Out of memory`
- Ollama crashes
- NOVA stops responding

**Solutions:**
1. **Reduce max_tokens**
   ```toml
   [intelligence]
   max_tokens = 256
   ```

2. **Reduce context window**
   ```toml
   [intelligence]
   num_ctx = 1024  # Down from 2048
   ```

3. **Switch to smaller model**
   ```bash
   ollama pull phi  # Smaller than llama3.2:1b
   ```
   Edit nova.toml:
   ```toml
   [intelligence]
   default_model = "phi"
   ```

4. **Close other applications**
   - Frees up RAM
   - Restart your computer if needed

5. **Upgrade RAM**
   Consider upgrading if persistent (need 8GB+ for 1B models)

---

## Tool Execution Issues

### "Tool execution timeout"

**Symptoms:**
- Error: `Tool execution timeout after 30 seconds`
- Tool never returns result

**Solutions:**
1. **Check tool availability**
   ```bash
   python verify_imports.py
   # Should show all 24 tools registered
   ```

2. **Try simpler tool** (e.g., `get_time`)
   If that works, specific tool has issue

3. **Increase timeout** (temporary)
   Edit `tools/base.py` or specific tool

4. **Check if tool process hung**
   ```bash
   tasklist | findstr python
   ```
   Kill stuck processes if needed

---

### "Tool not found / not registered"

**Symptoms:**
- Error: `Tool 'xyz' not in registry`
- Tool executes but returns error

**Solutions:**
1. **Verify all tools loaded**
   ```bash
   python verify_imports.py
   ```
   Should show "24 tools successfully registered"

2. **Check nova.toml tools list**
   Make sure tool name is in comma-separated list

3. **Restart NOVA**
   Sometimes registration fails on first load

---

### "Web search returns no results"

**Symptoms:**
- Web search tool executes but returns "No results"
- DuckDuckGo API not working

**Solutions:**
1. **Check internet connection**
   ```bash
   ping google.com
   ```

2. **Verify ddgs library**
   ```bash
   pip install --upgrade ddgs
   ```

3. **Try specific search**
   Instead of "what is X", try "X definition"

4. **Check if DuckDuckGo is blocking**
   Try again later (ddgs may rate-limit)

5. **Use alternative search engine**
   (Would require code modification)

---

## Session & Memory Issues

### "Session database corrupted"

**Symptoms:**
- Error: `Database is locked` or `Corrupted database`
- NOVA crashes on startup during session load

**Solutions:**
1. **Delete corrupted database**
   ```bash
   rm ~/.nova/sessions.db
   # NOVA will recreate on startup
   ```

2. **Backup and restore**
   ```bash
   # Before deleting, backup:
   copy %USERPROFILE%\.nova\sessions.db sessions.db.backup
   # Then delete original
   del %USERPROFILE%\.nova\sessions.db
   ```

3. **Check disk space**
   Ensure sufficient disk space for SQLite

4. **Restore from backup**
   If you have a backup from earlier

---

### "Conversation history not saving"

**Symptoms:**
- NOVA remembers conversation during session
- But after restart, history is gone

**Solutions:**
1. **Check if session folder exists**
   ```bash
   dir %USERPROFILE%\.nova\
   ```
   If not, create: `mkdir %USERPROFILE%\.nova\`

2. **Check file permissions**
   Ensure write permission to `.nova` directory

3. **Check disk space**
   May fail silently if disk full

4. **Look at logs**
   Check for SQLite errors (if logging enabled)

---

## General Troubleshooting

### "NOVA crashes immediately"

**Solutions:**
1. **Run with verbose output**
   ```bash
   python main.py -vvv  # If implemented
   ```
   Or check console for error messages

2. **Check specific subsystem**
   ```bash
   python verify_imports.py  # Tests all components
   ```

3. **Enable Python traceback**
   ```bash
   python -u main.py  # Unbuffered output
   ```

4. **Check system requirements**
   - Python 3.11+
   - Ollama running
   - Microphone working
   - Sufficient disk space

---

### "Strange behavior / random crashes"

**Solutions:**
1. **Update all dependencies**
   ```bash
   pip install -r requirements.txt --upgrade
   ```

2. **Reinstall from scratch**
   ```bash
   pip uninstall -r requirements.txt -y
   pip install -r requirements.txt
   ```

3. **Report issue**
   - [GitHub Issues](https://github.com/suki-stark-cmd/Nova/issues)
   - Include: Python version, OS, error message

---

## Debugging

### Enable Verbose Logging

Add to `main.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test Individual Components

```python
# Test STT
from speech.stt import STT
stt = STT()

# Test TTS
from speech.tts import TTS
tts = TTS()
tts.speak("Testing")

# Test Ollama
from engine.ollama import OllamaEngine
engine = OllamaEngine()
result = engine.generate([...], [])
print(result)

# Test Tool
from tools.builtin import WeatherTool
tool = WeatherTool()
result = tool.execute()
print(result)
```

### Check Logs

- Main logs: `~/.nova/nova.log` (if implemented)
- Ollama logs: Check Ollama terminal
- Python errors: Check terminal output

---

## Getting Help

1. **Check this guide first** - Most issues documented here
2. **Run verify_imports.py** - Confirms all systems working
3. **Search GitHub Issues** - Someone may have had same problem
4. **Open new issue** - Include:
   - OS and Python version
   - Error message and stack trace
   - Steps to reproduce
   - System specs (RAM, CPU, etc.)

---

**Last Updated:** May 13, 2026
