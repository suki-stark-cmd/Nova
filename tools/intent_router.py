"""Intent pre-router for Nova AI.

The llama3.2:1b model has only 2048 context tokens. Sending all 24 tool schemas
overwhelms it. This pre-router uses keyword matching to select only the 5-6 most
relevant tools for each query, dramatically improving tool-call accuracy.

This is the key difference from OpenJarvis which runs on 8B+ models that can
handle 40+ tools in context.
"""

from __future__ import annotations
import re
from typing import List, Set


# Keyword → tool name mapping (multiple keywords per tool)
_INTENT_MAP = {
    # Volume
    "volume_control": [
        "volume", "louder", "quieter", "loud", "quiet", "mute", "unmute",
        "sound", "audio level", "turn up", "turn down", "increase volume",
        "decrease volume", "lower volume", "raise volume",
    ],
    # Brightness
    "brightness_control": [
        "brightness", "bright", "dim", "dimmer", "brighter", "screen light",
        "display brightness", "screen brightness",
    ],
    # Media playback
    "media_control": [
        "pause", "resume", "play music", "next song", "skip", "previous",
        "prev track", "next track", "stop music", "pause music",
        "resume music", "play song", "stop", "stop video", "stop playback",
        "pause video", "play", "play video", "next", "back", "rewind",
    ],
    # Apple Music
    "apple_music": [
        "apple music", "itunes", "music app",
    ],
    # YouTube
    "play_youtube": [
        "youtube", "play video", "watch video", "play on youtube",
        "youtube video", "play songs", "play tamil", "play music video",
        "watch",
    ],
    # Edge browser
    "edge_browser": [
        "open website", "browse", "go to", "open url", "google",
        "search for", "open edge", "new tab", "close tab", "website",
        "open page", "navigate to",
    ],
    # App launcher
    "open_app": [
        "open", "launch", "start", "run app", "open app",
    ],
    # Notes
    "apple_notes": [
        "notes", "note", "take note", "write note", "show notes",
        "apple notes", "my notes",
    ],
    # Reminders
    "apple_reminders": [
        "reminder", "reminders", "remind me", "set reminder",
        "show reminders", "apple reminders",
    ],
    # Alarm / Timer
    "alarm_timer": [
        "alarm", "timer", "stopwatch", "set alarm", "set timer",
        "wake me", "countdown",
    ],
    # Screenshot
    "screenshot": [
        "screenshot", "screen capture", "capture screen", "take screenshot",
        "print screen", "snap screen",
    ],
    # Lock screen
    "lock_screen": [
        "lock screen", "lock computer", "lock pc", "lock laptop",
        "lock my", "lock the",
    ],
    # WiFi
    "wifi_toggle": [
        "wifi", "wi-fi", "internet", "wireless", "connect wifi",
        "disconnect wifi", "turn on wifi", "turn off wifi",
    ],
    # System info
    "system_info": [
        "battery", "cpu", "ram", "memory", "disk space", "storage",
        "ip address", "system info", "how much space", "disk usage",
        "charge level", "charge", "percentage", "laptop battery",
        "battery level", "battery life", "how much charge",
        "disk", "free space", "used space",
    ],
    # Window management
    "window_manage": [
        "minimize", "show desktop", "switch window", "alt tab",
        "close window", "desktop",
    ],
    # Weather
    "get_weather": [
        "weather", "temperature", "forecast", "rain", "sunny",
        "cloudy", "humidity", "wind",
    ],
    # Time
    "get_time": [
        "time", "date", "what day", "current time", "what time",
    ],
    # Calculator
    "calculator": [
        "calculate", "math", "plus", "minus", "multiply", "divide",
        "percent", "square root", "how much is", "what is",
    ],
    # Web search
    "web_search": [
        "search", "look up", "find", "who is", "what is", "tell me about",
        "information about", "facts about",
    ],
    # File read
    "file_read": [
        "read file", "open file", "show file", "contents of",
        "cat file", "view file",
    ],
    # File write
    "file_write": [
        "write file", "save file", "create file", "write to",
    ],
    # System command
    "system_command": [
        "run command", "execute command", "terminal", "powershell",
        "cmd", "command line",
    ],
    # HTTP request
    "http_request": [
        "http", "api", "fetch url", "request",
    ],
    # Think
    "think": [
        "think", "reason", "analyze", "consider",
    ],
}

# Pre-compile patterns for speed
_COMPILED = {
    tool: [re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE) for kw in keywords]
    for tool, keywords in _INTENT_MAP.items()
}

# Tools that should ALMOST ALWAYS be available (core assistants)
_ALWAYS_TOOLS = {"get_time", "get_weather", "calculator", "think"}

# Tools to exclude when specific category matches strongly
_EXCLUDE_WHEN = {
    "media_control": ["web_search"],  # "stop video" shouldn't call web_search
    "apple_reminders": ["web_search"],  # "set reminder" shouldn't search web
    "apple_notes": ["web_search"],  # "open notes" shouldn't search web
    "volume_control": ["web_search"],  # "turn up volume" shouldn't search
    "brightness_control": ["web_search"],  # "dim screen" shouldn't search
    "screenshot": ["web_search"],  # "take screenshot" shouldn't search
    "lock_screen": ["web_search"],  # "lock screen" shouldn't search
}

# Maximum tools to send to the model
MAX_TOOLS = 8


def route_intent(query: str) -> List[str]:
    """Given a user query, return the most relevant tool names.

    Returns at most MAX_TOOLS tool names, prioritized by keyword match score.
    Always includes _ALWAYS_TOOLS as baseline, except when primary tool
    explicitly excludes them.
    """
    scores: dict[str, int] = {}

    for tool_name, patterns in _COMPILED.items():
        for pat in patterns:
            if pat.search(query):
                scores[tool_name] = scores.get(tool_name, 0) + 1

    # Sort by score (highest first)
    matched = sorted(scores.keys(), key=lambda t: scores[t], reverse=True)

    # Build result: matched tools first, then always-on tools
    result: list[str] = []
    
    # Add highest-priority matched tool
    primary_tool = matched[0] if matched else None
    
    for t in matched:
        if t not in result:
            result.append(t)
    
    # Add always-on tools, respecting exclusions for primary tool
    for t in _ALWAYS_TOOLS:
        if t not in result:
            # Skip if primary tool excludes this tool
            if primary_tool and t in _EXCLUDE_WHEN.get(primary_tool, []):
                continue
            result.append(t)
    
    # web_search gets lower priority - only add if we have room and no better match
    if len(result) < MAX_TOOLS and primary_tool not in _EXCLUDE_WHEN and "web_search" not in result:
        # Check if query looks like a search query (who, what, find, search, etc.)
        search_patterns = [r'\bwho\b', r'\bwhat\b', r'\bfind\b', r'\bsearch\b', 
                          r'\blook\b', r'\binformation\b', r'\bfacts?\b']
        if any(re.search(pat, query, re.IGNORECASE) for pat in search_patterns):
            result.append("web_search")

    return result[:MAX_TOOLS]


__all__ = ["route_intent", "MAX_TOOLS"]
