# NOVA Usage Guide

## Basic Voice Commands

### Volume Control
```
"Turn up the volume"                 → Volume increased
"Set volume to 75 percent"           → Volume set to 75%
"Mute the speaker"                   → Volume muted
"Make it quieter"                    → Volume decreased
```

### Screen Brightness
```
"Make the screen brighter"           → Brightness increased
"Dim the screen"                     → Brightness decreased
"Set brightness to 40 percent"       → Brightness set to 40%
```

### System Information
```
"What's my battery level?"           → Battery at 85%
"How much disk space do I have?"     → Disk: 200GB free of 500GB
"Check system info"                  → Display CPU, RAM, disk, IP
"What's my IP address?"              → Display current IP
```

### Time & Date
```
"What time is it?"                   → It's 2:45 PM
"What's today's date?"               → May 13, 2026
"Tell me the current time"           → Display time/date
```

### Weather
```
"What's the weather like?"           → Weather in current location
"Temperature?"                       → Current temperature
"Will it rain?"                      → Rain forecast
```

### Applications
```
"Open Spotify"                       → Launch Spotify
"Start Visual Studio Code"           → Open VS Code
"Launch Chrome"                      → Open browser
"Open YouTube"                       → Open YouTube in Edge
"Open Apple Music"                   → Open Apple Music
```

### Notes & Reminders
```
"Open my notes"                      → Open Apple Notes
"Show reminders"                     → Open Apple Reminders
"Open iCloud reminders"              → Open Apple Reminders
```

### Screenshot
```
"Take a screenshot"                  → Save screenshot to Desktop
"Capture the screen"                 → Screenshot taken
```

### Media Control
```
"Play the music"                     → Start media playback
"Pause"                              → Pause current playback
"Next song"                          → Skip to next track
"Previous track"                     → Go to previous track
"Stop the video"                     → Stop playback
```

### Search
```
"Search for Python tutorials"        → Display search results
"Look up Mount Everest"              → Show information
"Who is the president?"              → Display answer
"What is machine learning?"          → Explain concept
```

### Calculations
```
"What's 15 plus 27?"                 → 42
"Calculate 100 divided by 5"         → 20
"What's 25 percent of 400?"          → 100
```

### Window Management
```
"Minimize all windows"               → Hide all open windows
"Show desktop"                       → Clear desktop
"Switch window"                      → Bring up window switcher
"Close this window"                  → Close current window
```

### WiFi
```
"Turn off WiFi"                      → WiFi disabled
"Connect to WiFi"                    → WiFi enabled
"Enable WiFi"                        → WiFi turned on
```

### Lock Screen
```
"Lock the screen"                    → Screen locked
"Lock my computer"                   → Computer locked
```

---

## Advanced Usage

### Combining Commands

Some queries will use multiple tools:
```
You: "What's the time and weather?"
[Tool] get_time({...})
[Tool] get_weather({...})
NOVA: It's 2:45 PM and sunny with 72 degrees.
```

### Natural Speech Patterns

NOVA understands casual variations:
```
"Hey, turn up sound"                 → Understood
"Make it louder, please"             → Volume up
"My screen too bright"               → Dimmer
"I need brightness"                  → Increase brightness
```

### Follow-up Commands

Context persists across commands:
```
You: "What's my battery?"
NOVA: Battery at 85%.
You: "What about disk space?"        → Uses same system_info tool
NOVA: Disk 200GB free of 500GB.
```

### Session Memory

NOVA remembers conversation context:
```
You: "Remember I need to call mom at 3 PM"
You (later): "What did I ask you to remember?"
NOVA: You wanted to remember to call mom at 3 PM.
```

---

## Tips & Tricks

### Better Voice Recognition

1. **Speak Clearly** - Whisper model works best with clear speech
2. **Use Pauses** - VAD needs silence to confirm end of utterance
3. **Quiet Environment** - Less background noise = better accuracy
4. **Good Microphone** - Improve accuracy significantly
5. **Normal Pace** - Don't rush or drag words

### Optimal Commands

- **Be Specific**: "Play Starboy on YouTube" (better than "play music")
- **Use Tool Names**: "Set volume" (better than "make audio louder")
- **Short Queries**: "What time?" (better than "I was wondering if you could tell me...") 
- **Natural Language**: NOVA understands intent, not exact keywords

### Performance Tips

- **Offload Ollama**: Run Ollama on separate machine via SSH for faster inference
- **Disable Unused Tools**: Edit `nova.toml` to only load needed tools
- **Close Background Apps**: Frees up RAM for LLM inference
- **Use "small" STT**: Faster than medium/large but still accurate

---

## Interactive Commands

### Text Mode

Instead of voice input, type commands:

```
NOVA: Nova is ready. How can I help you?
You: What time is it?
NOVA: It's 2:45 PM, Wednesday.
You: Set brightness to 60
NOVA: Brightness set to 60%.
You: quit
```

### Exiting NOVA

```
You: quit
You: exit
You: stop
You: shutdown
You: bye
```

Any of these will gracefully exit NOVA and save session.

---

## Error Handling

### "I'm sorry, I couldn't find..."

Usually means:
- Web search returned no results
- Tool failed unexpectedly
- Request cannot be fulfilled

**Try:** Rephrase or be more specific

### "Can't reach the internet"

Means:
- Edge-TTS failed (no internet)
- Web search unavailable
- URL fetch failed

**Try:** 
- Check internet connection
- Try offline-friendly command (volume, brightness, time)
- pyttsx3 should handle TTS fallback

### "That tool isn't available"

Means:
- Tool didn't load during startup
- Tool was explicitly disabled
- Tool failed to register

**Try:** Check `verify_imports.py` output and restart NOVA

---

## Customization

### Change Default Voice

Edit `nova.toml`:
```toml
[speech]
voice = "en-US-AriaNeural"
```

Available voices: en-US-GuyNeural, en-US-AriaNeural, etc.

### Adjust Response Speed

Edit `nova.toml`:
```toml
[speech]
rate = "1.5"  # Faster
# or
rate = "0.75" # Slower
```

### Disable Tools

Edit `nova.toml`:
```toml
[agent]
tools = "volume_control,brightness_control,get_time,get_weather,calculator"
# Removed: media_control, open_app, etc.
```

### Change Model Temperature

Edit `nova.toml`:
```toml
[intelligence]
temperature = 0.1  # More deterministic responses
# or
temperature = 0.7  # More creative responses
```

---

## Common Scenarios

### Scenario 1: Using NOVA as Alarm Clock

```
You: "Set an alarm for 7 AM"
[Tool] alarm_timer({...})
NOVA: Opening alarm in Windows Clock.

You: "What time is it now?"
[Tool] get_time({...})
NOVA: It's 6:45 PM, May 13, 2026.
```

### Scenario 2: Quick Research

```
You: "Who invented the telephone?"
[Tool] web_search({"query": "who invented telephone"})
NOVA: Alexander Graham Bell invented the telephone in 1876.

You: "Tell me more about him"
[Tool] web_search({"query": "Alexander Graham Bell biography"})
NOVA: Alexander Graham Bell was a Scottish-born inventor...
```

### Scenario 3: Workflow Automation

```
You: "Open Visual Studio Code"
[Tool] open_app({"app_name": "VS Code"})
NOVA: Opened VS Code.

You: "Take a screenshot"
[Tool] screenshot({})
NOVA: Screenshot saved.

You: "Open the last screenshot"
[Tool] file_read({"path": "Desktop\\screenshot_*.png"})
NOVA: Image opened.
```

### Scenario 4: Gaming Session

```
You: "Minimize all windows"
[Tool] window_manage({"action": "minimize_all"})
NOVA: All windows minimized.

You: "Set volume to 80"
[Tool] volume_control({"action": "set", "level": "80"})
NOVA: Volume set to 80%.

You: "Increase brightness"
[Tool] brightness_control({"action": "increase"})
NOVA: Brightness increased.
```

---

## Privacy & Security

NOVA keeps all data locally:
- ✅ No cloud uploads
- ✅ No telemetry sent
- ✅ Conversation stored locally in SQLite
- ✅ Models run locally via Ollama
- ✅ Speech synthesis cached locally when offline

Your data never leaves your computer!

---

## Keyboard Shortcuts (Text Mode)

```
Ctrl+C         Exit NOVA
Up Arrow       Previous command in history (if implemented)
Tab            Command autocomplete (if implemented)
```

---

## Advanced: Custom Tools

See [docs/API.md](API.md) to create custom tools for NOVA.

---

**Last Updated:** May 13, 2026
