# Nova AI — Voice Command Reference

> **24 tools** across 5 categories. Say any phrase naturally — Nova's intent router matches it to the right action.

---

## 🔊 Windows Controls

### Volume Control → `volume_control`

| Say This... | Action |
|---|---|
| "Turn up the volume" | Increase volume ~10% |
| "Make it louder" | Increase volume |
| "Turn down the volume" | Decrease volume |
| "Make it quieter" | Decrease volume |
| "Mute the sound" | Toggle mute on |
| "Unmute" | Toggle mute off |
| "Set volume to 50" | Set exact level |
| "Lower the volume" | Decrease volume |
| "Raise the volume" | Increase volume |

### Brightness Control → `brightness_control`

| Say This... | Action |
|---|---|
| "Increase the brightness" | +15% brightness |
| "Make it brighter" | +15% brightness |
| "Dim the screen" | -15% brightness |
| "Make it dimmer" | -15% brightness |
| "Set brightness to 70" | Set exact level |
| "Lower the screen light" | -15% brightness |

### Lock Screen → `lock_screen`

| Say This... | Action |
|---|---|
| "Lock my computer" | Lock screen (Win+L) |
| "Lock the screen" | Lock screen |
| "Lock my PC" | Lock screen |
| "Lock the laptop" | Lock screen |

### Screenshot → `screenshot`

| Say This... | Action |
|---|---|
| "Take a screenshot" | Save screenshot to Desktop |
| "Capture the screen" | Save screenshot |
| "Screenshot" | Save screenshot |
| "Screen capture" | Save screenshot |

### Wi-Fi Toggle → `wifi_toggle`

| Say This... | Action |
|---|---|
| "Turn on Wi-Fi" | Enable Wi-Fi adapter |
| "Turn off Wi-Fi" | Disable Wi-Fi adapter |
| "Disable wireless" | Disable Wi-Fi |
| "Connect to internet" | Enable Wi-Fi |

### Window Management → `window_manage`

| Say This... | Action |
|---|---|
| "Minimize all windows" | Win+D effect |
| "Show desktop" | Minimize everything |
| "Show me the desktop" | Minimize everything |
| "Switch window" | Alt+Tab |
| "Close this window" | Alt+F4 |
| "Go to desktop" | Minimize everything |

### System Info → `system_info`

| Say This... | Action |
|---|---|
| "What's my battery level" | Show battery % |
| "How much charge is left" | Show battery % |
| "Check my battery" | Show battery % |
| "How much RAM am I using" | Show memory usage |
| "What's my CPU usage" | Show CPU load |
| "How much disk space" | Show C: drive usage |
| "What's my IP address" | Show local IP |
| "Am I connected to Wi-Fi" | Show Wi-Fi status |
| "System info" | Show everything |

### Open App → `open_app`

| Say This... | Action |
|---|---|
| "Open Calculator" | Launch Calculator |
| "Open Settings" | Launch Settings |
| "Launch Notepad" | Launch Notepad |
| "Open File Explorer" | Launch Explorer |
| "Start Terminal" | Launch Windows Terminal |
| "Open Paint" | Launch Paint |
| "Open VS Code" | Launch Visual Studio Code |
| "Open Task Manager" | Launch Task Manager |
| "Open Apple Music" | Launch Apple Music app |
| "Open WhatsApp" | Launch WhatsApp |

> **Supported apps:** Edge, Settings, Calculator, Notepad, Paint, File Explorer, Terminal, PowerShell, Apple Music, Apple TV, Apple Devices, iCloud, WhatsApp, Telegram, Discord, Teams, Photos, Camera, Word, Excel, PowerPoint, Outlook, VS Code, Snipping Tool

---

## 🎵 Media & Apple

### Media Playback → `media_control`
*(Works with any active player — Apple Music, YouTube, Spotify, etc.)*

| Say This... | Action |
|---|---|
| "Pause the music" | Play/Pause toggle |
| "Resume playing" | Play/Pause toggle |
| "Play" | Play/Pause toggle |
| "Next song" | Skip to next track |
| "Skip this song" | Skip to next track |
| "Previous track" | Go to previous track |
| "Stop the music" | Stop playback |

### Apple Music → `apple_music`

| Say This... | Action |
|---|---|
| "Open Apple Music" | Launch Apple Music app |
| "Play on Apple Music" | Open app + search |
| "Search Tamil songs on Apple Music" | Open + search query |

### Apple Notes → `apple_notes`
*(Opens via iCloud in Edge)*

| Say This... | Action |
|---|---|
| "Open my notes" | Open iCloud Notes |
| "Show notes" | Open iCloud Notes |
| "Take a note" | Open iCloud Notes |
| "Apple Notes" | Open iCloud Notes |

### Apple Reminders → `apple_reminders`
*(Opens via iCloud in Edge)*

| Say This... | Action |
|---|---|
| "Show my reminders" | Open iCloud Reminders |
| "Open reminders" | Open iCloud Reminders |
| "Set a reminder" | Open iCloud Reminders |

### Alarm & Timer → `alarm_timer`
*(Uses Windows Clock app)*

| Say This... | Action |
|---|---|
| "Set an alarm" | Open Alarms |
| "Set a timer for 5 minutes" | Open Timer |
| "Start a stopwatch" | Open Stopwatch |
| "Wake me up at 7" | Open Alarms |
| "Set a countdown" | Open Timer |

---

## 🌐 Browser & YouTube

### Edge Browser → `edge_browser`

| Say This... | Action |
|---|---|
| "Open Google" | Open google.com in Edge |
| "Open google.com" | Navigate to URL |
| "Go to youtube.com" | Navigate to URL |
| "Search for Python tutorials" | Google search in Edge |
| "Open a new tab" | New tab in Edge |
| "Close this tab" | Close current tab |
| "Browse to Wikipedia" | Navigate to site |

### YouTube (in Edge) → `play_youtube`

| Say This... | Action |
|---|---|
| "Play Tamil songs on YouTube" | Search & play first result |
| "Play a video" | Open YouTube search |
| "Watch cooking tutorial" | Search & play |
| "Play music videos" | Search & play |
| "YouTube search for cats" | Search & play |

---

## 📊 Productivity

### Weather → `get_weather`

| Say This... | Action |
|---|---|
| "What's the weather" | Current weather |
| "Is it going to rain" | Weather forecast |
| "Temperature in Karur" | City-specific weather |
| "Weather forecast" | Current conditions |

### Time & Date → `get_time`

| Say This... | Action |
|---|---|
| "What time is it" | Current time |
| "What's the date" | Current date |
| "What day is today" | Day + date |

### Calculator → `calculator`

| Say This... | Action |
|---|---|
| "Calculate 15 times 23" | Math: 345 |
| "What is 5 plus 3" | Math: 8 |
| "Square root of 144" | Math: 12 |
| "What is 20 percent of 500" | Math: 100 |

### Web Search → `web_search`

| Say This... | Action |
|---|---|
| "Search for AI news" | DuckDuckGo search |
| "Who is Elon Musk" | Web search |
| "Tell me about quantum computing" | Web search |
| "Look up recipes for biryani" | Web search |

### Think (Reasoning) → `think`

| Say This... | Action |
|---|---|
| "Think about this problem" | Internal reasoning scratchpad |
| "Analyze this situation" | Chain-of-thought processing |

---

## 📁 System & Files

### File Read → `file_read`

| Say This... | Action |
|---|---|
| "Read the file at path" | Display file contents |
| "Show me the contents of" | Read text file |

### File Write → `file_write`

| Say This... | Action |
|---|---|
| "Write to a file" | Create/overwrite file |
| "Save this to a file" | Write content |
| "Append to the file" | Append mode |

### System Command → `system_command`

| Say This... | Action |
|---|---|
| "Run command dir" | Execute shell command |
| "Execute powershell" | Run PS command |

> ⚠️ **Security:** Dangerous commands (`rm -rf`, `format`, `del /s`) are blocked. Sensitive files (`.env`, SSH keys, credentials) cannot be read or written.

### HTTP Request → `http_request`

| Say This... | Action |
|---|---|
| "Fetch this URL" | HTTP GET request |
| "Make an API call" | HTTP request |

---

## ⚙️ How It Works

```
Your Voice ──→ [Whisper STT] ──→ [Intent Router] ──→ [llama3.2:1b + Tools] ──→ [Edge-TTS] ──→ Speaker
                                       │
                                 Selects top 8 of 24
                                 tools per query for
                                 optimal 1B model
                                 accuracy
```

1. **You speak** → Whisper transcribes to text
2. **Intent Router** scans for keywords and selects the **top 8 most relevant tools** (out of 24)
3. **llama3.2:1b** receives only those 8 tool schemas, picks the right one, and calls it
4. **Tool executes** (PowerShell, media keys, browser launch, etc.)
5. **Nova speaks** the result back via Edge-TTS

> **Why only 8 tools?** The 1B model has 2048 context tokens. Sending all 24 tool schemas would overflow the context window. The intent router solves this by pre-filtering.

---

## 🚫 Excluded (by user request)

| Command | Status |
|---|---|
| Sleep / Shutdown / Restart | ❌ Excluded (do later) |
| Spotify | ❌ Not used (using Apple Music + YouTube) |
