# NOVA Tool API Reference

Complete reference for all 24 built-in tools and custom tool development.

---

## Audio Tools

### volume_control
Control system volume.

**Parameters:**
- `action` (string): "up", "down", "set", "mute", "unmute", "toggle_mute"
- `level` (integer, optional): 0-100 for "set" action

**Examples:**
```python
{"action": "up"}                    # Increase volume
{"action": "down"}                  # Decrease volume
{"action": "set", "level": "75"}   # Set to 75%
{"action": "mute"}                  # Mute
```

**Returns:**
```
"Volume increased."
"Volume set to 75%."
"Volume adjustment failed." (error)
```

---

### media_control
Control media playback (music/video).

**Parameters:**
- `action` (string): "play", "pause", "next", "previous", "stop"

**Examples:**
```python
{"action": "play"}     # Start playback
{"action": "next"}     # Next track
{"action": "pause"}    # Pause
```

**Returns:**
```
"Music playing."
"Next track."
"Playback paused." (error)
```

---

## Display Tools

### brightness_control
Control screen brightness.

**Parameters:**
- `action` (string): "up", "down", "set"
- `level` (integer, optional): 0-100 for "set" action

**Examples:**
```python
{"action": "up"}                    # Increase brightness
{"action": "down"}                  # Decrease brightness
{"action": "set", "level": "50"}   # Set to 50%
```

**Returns:**
```
"Brightness increased."
"Screen set to 50%."
"Brightness adjustment failed." (error)
```

---

### screenshot
Take a screenshot.

**Parameters:** (none)

**Example:**
```python
{}
```

**Returns:**
```
"Screenshot saved."
"Screenshot failed." (error)
```

---

## Windows Control Tools

### window_manage
Manage open windows.

**Parameters:**
- `action` (string): "minimize_all", "show_desktop", "switch_window", "close"

**Examples:**
```python
{"action": "minimize_all"}   # Minimize all windows
{"action": "show_desktop"}   # Show desktop
{"action": "switch_window"}  # Alt+Tab switcher
```

**Returns:**
```
"All windows minimized."
"Desktop shown."
"Window switcher opened."
```

---

### lock_screen
Lock the computer.

**Parameters:** (none)

**Example:**
```python
{}
```

**Returns:**
```
"Screen locked."
"Lock failed." (error)
```

---

### open_app
Launch an application.

**Parameters:**
- `app_name` (string): Application name (e.g., "Spotify", "VS Code", "Chrome")

**Supported Apps:** 30+ pre-configured (Chrome, Firefox, Edge, Spotify, VS Code, Python IDLE, Discord, Slack, Telegram, etc.)

**Examples:**
```python
{"app_name": "Spotify"}        # Launch Spotify
{"app_name": "VS Code"}        # Launch Visual Studio Code
{"app_name": "Chrome"}         # Launch Chrome
```

**Returns:**
```
"Opened Spotify."
"Opening VS Code."
"App not found." (error)
```

---

## System Tools

### system_info
Get system information.

**Parameters:** (none)

**Example:**
```python
{}
```

**Returns:**
```
"Battery: 85% | CPU: 35% | RAM: 8GB/16GB | Disk: 400GB/500GB free | IP: 192.168.1.100"
```

---

### wifi_toggle
Toggle WiFi on/off.

**Parameters:**
- `state` (string): "on" or "off"

**Examples:**
```python
{"state": "on"}   # Turn on WiFi
{"state": "off"}  # Turn off WiFi
```

**Returns:**
```
"WiFi turned on."
"WiFi turned off."
"WiFi toggle failed." (error)
```

---

### alarm_timer
Open Windows Clock (alarms/timers).

**Parameters:** (none)

**Example:**
```python
{}
```

**Returns:**
```
"Windows Clock opened."
```

---

## Application Tools

### apple_music
Open Apple Music.

**Parameters:**
- `action` (string, optional): "search", "open"
- `query` (string, optional): Search query

**Examples:**
```python
{}                                    # Just open app
{"action": "search", "query": "Drake"}  # Search Drake songs
```

**Returns:**
```
"Apple Music opened."
"Searching: Drake..."
```

---

### edge_browser
Open Microsoft Edge with URL/search.

**Parameters:**
- `action` (string): "open", "search", "new_tab", "close"
- `query` (string, optional): URL or search query

**Examples:**
```python
{"action": "open", "query": "https://github.com"}  # Open URL
{"action": "search", "query": "Python"}            # Search
{"action": "new_tab"}                              # New tab
```

**Returns:**
```
"Opening github.com in Edge."
"Searching for Python."
"New tab opened."
```

---

### play_youtube
Search and play YouTube videos in Edge.

**Parameters:**
- `query` (string): Video/song name

**Examples:**
```python
{"query": "Starboy The Weeknd"}
{"query": "Python tutorials"}
```

**Returns:**
```
"Searching YouTube for Starboy..."
"Playing videos."
```

---

### apple_notes
Open Apple Notes in Edge.

**Parameters:**
- `action` (string, optional): "open"

**Example:**
```python
{}
```

**Returns:**
```
"Apple Notes opened in Edge."
```

---

### apple_reminders
Open Apple Reminders in Edge.

**Parameters:**
- `action` (string, optional): "open"

**Example:**
```python
{}
```

**Returns:**
```
"Apple Reminders opened in Edge."
```

---

## Information Tools

### get_time
Get current time and date.

**Parameters:** (none)

**Example:**
```python
{}
```

**Returns:**
```
"Time: 2:45 PM, Date: Wednesday, May 13, 2026"
```

---

### get_weather
Get current weather.

**Parameters:** (none) (uses current location via wttr.in)

**Example:**
```python
{}
```

**Returns:**
```
"+72°F | Sunny | 60% humidity | Wind 5mph"
```

---

### calculator
Perform mathematical calculations.

**Parameters:**
- `expression` (string): Math expression

**Examples:**
```python
{"expression": "15 + 27"}           # 42
{"expression": "100 / 5"}           # 20
{"expression": "sqrt(144)"}         # 12
{"expression": "(50 * 3) - 25"}     # 125
```

**Returns:**
```
"42"
"20"
"12"
"Error: Invalid expression" (error)
```

---

### web_search
Search the web using DuckDuckGo.

**Parameters:**
- `query` (string): Search query
- `max_results` (integer, optional): Number of results (default 3)

**Examples:**
```python
{"query": "Python async programming"}
{"query": "machine learning", "max_results": 5}
```

**Returns:**
```
"**Python Async Programming Guide**
https://realpython.com/async-io-python/
Complete guide to async/await in Python..."
```

---

## File Tools

### file_read
Read a file (with security checks).

**Parameters:**
- `path` (string): File path

**Security:** 
- Max 1MB file size
- Blocks .env, SSH keys, credentials
- Blocks system files

**Example:**
```python
{"path": "C:\\Users\\User\\Desktop\\notes.txt"}
```

**Returns:**
```
"[File contents up to 1MB]"
"Access denied: sensitive file." (error)
"File not found." (error)
```

---

### file_write
Write to a file (with security checks).

**Parameters:**
- `path` (string): File path
- `content` (string): Content to write

**Security:** Blocks sensitive file paths

**Example:**
```python
{"path": "C:\\Users\\User\\Desktop\\log.txt", "content": "Test content"}
```

**Returns:**
```
"File written successfully."
"Access denied." (error)
```

---

## Command Tools

### system_command
Execute system commands (with filtering).

**Parameters:**
- `command` (string): Command to run

**Security:** Blocks dangerous commands (rm -rf, format, del /s, etc.)

**Example:**
```python
{"command": "echo Hello World"}
```

**Returns:**
```
"Hello World"
"Access denied: dangerous command." (error)
```

---

### http_request
Make HTTP GET/POST requests.

**Parameters:**
- `method` (string): "GET" or "POST"
- `url` (string): Target URL
- `data` (string, optional): POST data

**Examples:**
```python
{"method": "GET", "url": "https://api.example.com/data"}
{"method": "POST", "url": "https://api.example.com/submit", "data": "{\"key\": \"value\"}"}
```

**Returns:**
```
"[Response body]"
"Connection error." (error)
```

---

## AI Tools

### think
Reasoning scratchpad for model to think through problems.

**Parameters:**
- `reasoning` (string): Internal reasoning

**Example:**
```python
{"reasoning": "Let me break this down..."}
```

**Returns:**
```
"[Model's thoughts]"
```

---

## Deprecated Tools

### play_youtube_deprecated (DO NOT USE)
Old YouTube tool - use `play_youtube` instead.

---

## Creating Custom Tools

### Basic Tool Template

```python
from tools.base import BaseTool, ToolResult, ToolSpec
from typing import Any

class MyCustomTool(BaseTool):
    """Description of what your tool does."""
    
    tool_id = "my_tool_name"
    
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="my_tool_name",
            description="What this tool does",
            parameters={
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "First parameter"
                    },
                    "param2": {
                        "type": "integer",
                        "description": "Second parameter"
                    }
                },
                "required": ["param1"]
            },
            timeout_seconds=10.0
        )
    
    def execute(self, **params: Any) -> ToolResult:
        try:
            param1 = params.get("param1", "")
            param2 = params.get("param2", 0)
            
            # Your implementation here
            result = f"Processed {param1}"
            
            return ToolResult(
                tool_name="my_tool_name",
                content=result,
                success=True
            )
        except Exception as e:
            return ToolResult(
                tool_name="my_tool_name",
                content="Operation failed.",
                success=False
            )


# Register the tool
from tools.registry import tool_collection
tool_collection.add(MyCustomTool())
```

### Registering Custom Tools

Add to `tools/builtin.py` in `register_builtin_tools()`:

```python
def register_builtin_tools():
    """Register all built-in tools."""
    tools = [
        WeatherTool(),
        # ... existing tools ...
        MyCustomTool(),  # Your new tool
    ]
    for tool in tools:
        try:
            tool_collection.add(tool)
        except ValueError as e:
            logger.warning(f"Tool already registered: {e}")
```

### Tool Development Best Practices

1. **Keep timeouts reasonable** (5-30 seconds)
2. **Return user-friendly messages** (not technical)
3. **Handle all exceptions** gracefully
4. **Test thoroughly** before registering
5. **Document parameters** clearly
6. **Security first** (validate inputs, check permissions)

---

## Error Handling

All tools return `ToolResult` objects:

```python
ToolResult(
    tool_name="tool_id",
    content="User-friendly message",
    success=True/False,
    execution_time=seconds  # Optional
)
```

Tool errors are caught and logged; NOVA continues with other tools.

---

**Last Updated:** May 13, 2026
