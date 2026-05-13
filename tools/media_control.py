"""Media control tools for Nova AI.

Provides voice control for:
  - Apple Music (play/pause/next/skip/search via media keys + app launch)
  - Edge Browser (open URL, search, new tab)
  - YouTube in Edge (search and play)
  - Media playback keys (play/pause/next/prev — works with ANY media app)
  - Apple Notes (open/create note via iCloud)
  - Apple Reminders (open via iCloud)
  - Alarms & Timers (Windows Clock app)
"""

from __future__ import annotations
import subprocess
import time
import urllib.parse
import re
from typing import Any

from tools.base import BaseTool
from core.types import ToolResult, ToolSpec


# ═══════════════════════════════════════════════════════════════
# Media Playback Control (works with ANY active media player)
# ═══════════════════════════════════════════════════════════════

class MediaPlaybackTool(BaseTool):
    """Control any active media player via Windows media keys."""

    tool_id = "media_control"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="media_control",
            description=(
                "Control media playback (works with Apple Music, Edge YouTube, or any player). "
                "Actions: 'play_pause' (toggle play/pause), 'next' (next track), "
                "'previous' (previous track), 'stop'. "
                "Use when user says 'pause the music', 'play', 'next song', "
                "'skip', 'previous track', 'resume music', 'stop music'."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action: 'play_pause', 'next', 'previous', or 'stop'.",
                    },
                },
                "required": ["action"],
            },
        )

    # Windows virtual key codes for media keys
    _KEYS = {
        "play_pause": 0xB3,   # VK_MEDIA_PLAY_PAUSE
        "play": 0xB3,
        "pause": 0xB3,
        "next": 0xB0,         # VK_MEDIA_NEXT_TRACK
        "skip": 0xB0,
        "previous": 0xB1,     # VK_MEDIA_PREV_TRACK
        "prev": 0xB1,
        "stop": 0xB2,         # VK_MEDIA_STOP
    }

    def execute(self, **params: Any) -> ToolResult:
        action = params.get("action", "play_pause").lower().strip()
        vk = self._KEYS.get(action)
        if vk is None:
            return ToolResult(tool_name="media_control",
                              content=f"Unknown action: {action}. Use play_pause/next/previous/stop.",
                              success=False)
        try:
            import ctypes
            KEYEVENTF_EXTENDEDKEY = 0x0001
            KEYEVENTF_KEYUP = 0x0002
            ctypes.windll.user32.keybd_event(vk, 0, KEYEVENTF_EXTENDEDKEY, 0)
            ctypes.windll.user32.keybd_event(vk, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)

            action_name = {
                0xB3: "play/pause toggled",
                0xB0: "skipped to next track",
                0xB1: "went to previous track",
                0xB2: "stopped playback",
            }.get(vk, action)
            return ToolResult(tool_name="media_control", content=f"Media: {action_name}.")
        except Exception as e:
            return ToolResult(tool_name="media_control", content=f"Error: {e}", success=False)


# ═══════════════════════════════════════════════════════════════
# Apple Music Control
# ═══════════════════════════════════════════════════════════════

class AppleMusicTool(BaseTool):
    """Open Apple Music and search for songs/artists/albums."""

    tool_id = "apple_music"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="apple_music",
            description=(
                "Open Apple Music app and optionally search for a song, artist, or album. "
                "Use when user says 'play on Apple Music', 'open Apple Music', "
                "'play Tamil songs on Apple Music', 'search on Apple Music'. "
                "For simple play/pause/next/previous of already playing music, use media_control instead."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Optional search query (song, artist, or album name).",
                    },
                    "action": {
                        "type": "string",
                        "description": "Action: 'open' (just open app), 'search' (search for query). Default: 'search'.",
                    },
                },
                "required": [],
            },
        )

    def execute(self, **params: Any) -> ToolResult:
        query = params.get("query", "")
        action = params.get("action", "search" if query else "open").lower()

        try:
            # Launch Apple Music Windows app
            subprocess.Popen(
                "start shell:AppsFolder\\AppleInc.AppleMusic_nzyj5cx40ttqa!App",
                shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            time.sleep(1.5)  # Wait for app to focus

            if query and action == "search":
                # Use Apple Music web search as fallback
                url = f"https://music.apple.com/search?term={urllib.parse.quote(query)}"
                subprocess.Popen(f"start msedge \"{url}\"", shell=True,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return ToolResult(tool_name="apple_music",
                                  content=f"Opened Apple Music and searching for '{query}'.")

            return ToolResult(tool_name="apple_music", content="Apple Music opened.")

        except Exception as e:
            return ToolResult(tool_name="apple_music", content=f"Error: {e}", success=False)


# ═══════════════════════════════════════════════════════════════
# Edge Browser Control
# ═══════════════════════════════════════════════════════════════

class EdgeBrowserTool(BaseTool):
    """Control Microsoft Edge — open URLs, search, new tab."""

    tool_id = "edge_browser"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="edge_browser",
            description=(
                "Control Microsoft Edge browser. "
                "Actions: 'open' (open a URL), 'search' (search the web), "
                "'new_tab' (open a new tab), 'close' (close current tab). "
                "Use when user says 'open google', 'search for something', "
                "'go to website', 'open a new tab', 'browse to'."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "'open', 'search', 'new_tab', or 'close'.",
                    },
                    "url": {
                        "type": "string",
                        "description": "URL to open (for 'open' action).",
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query (for 'search' action).",
                    },
                },
                "required": ["action"],
            },
        )

    def execute(self, **params: Any) -> ToolResult:
        action = params.get("action", "open").lower().strip()
        try:
            if action == "open":
                url = params.get("url", "") or params.get("query", "")
                if not url:
                    subprocess.Popen("start msedge", shell=True,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return ToolResult(tool_name="edge_browser", content="Edge opened.")
                # Add https if missing
                if not url.startswith(("http://", "https://", "www.")):
                    url = f"https://www.{url}"
                elif url.startswith("www."):
                    url = f"https://{url}"
                subprocess.Popen(f'start msedge "{url}"', shell=True,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return ToolResult(tool_name="edge_browser", content=f"Opened {url} in Edge.")

            elif action == "search":
                query = params.get("query", "") or params.get("url", "")
                if not query:
                    return ToolResult(tool_name="edge_browser",
                                      content="No search query provided.", success=False)
                url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
                subprocess.Popen(f'start msedge "{url}"', shell=True,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return ToolResult(tool_name="edge_browser",
                                  content=f"Searching for '{query}' in Edge.")

            elif action in ("new_tab", "newtab"):
                subprocess.Popen("start msedge --new-tab", shell=True,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return ToolResult(tool_name="edge_browser", content="New tab opened in Edge.")

            elif action == "close":
                ps = '(New-Object -ComObject WScript.Shell).SendKeys("^w")'
                subprocess.run(["powershell", "-Command", ps], capture_output=True, timeout=5)
                return ToolResult(tool_name="edge_browser", content="Tab closed.")

            else:
                return ToolResult(tool_name="edge_browser",
                                  content=f"Unknown action: {action}.", success=False)

        except Exception as e:
            return ToolResult(tool_name="edge_browser", content=f"Error: {e}", success=False)


# ═══════════════════════════════════════════════════════════════
# YouTube (in Edge)
# ═══════════════════════════════════════════════════════════════

class YouTubeEdgeTool(BaseTool):
    """Play YouTube videos in Microsoft Edge."""

    tool_id = "play_youtube"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="play_youtube",
            description=(
                "Search and play a video or song on YouTube in Edge browser. "
                "Use when user says 'play on YouTube', 'play video', "
                "'play Tamil songs', 'play music video', 'YouTube search', "
                "'watch on YouTube'."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for YouTube.",
                    },
                },
                "required": ["query"],
            },
        )

    def execute(self, **params: Any) -> ToolResult:
        query = params.get("query", "")
        if not query:
            return ToolResult(tool_name="play_youtube", content="No query.", success=False)
        try:
            import urllib.request
            search_url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)
            req = urllib.request.Request(search_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
            vid_match = re.search(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
            if vid_match:
                play_url = f"https://www.youtube.com/watch?v={vid_match.group(1)}"
                subprocess.Popen(f'start msedge "{play_url}"', shell=True,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return ToolResult(tool_name="play_youtube",
                                  content=f"Playing '{query}' on YouTube in Edge.")

            subprocess.Popen(f'start msedge "{search_url}"', shell=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return ToolResult(tool_name="play_youtube",
                              content=f"Opened YouTube search for '{query}' in Edge.")
        except Exception as e:
            return ToolResult(tool_name="play_youtube", content=f"Error: {e}", success=False)


# ═══════════════════════════════════════════════════════════════
# Apple Notes & Reminders (via iCloud Web)
# ═══════════════════════════════════════════════════════════════

class AppleNotesTool(BaseTool):
    """Open Apple Notes via iCloud web in Edge."""

    tool_id = "apple_notes"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="apple_notes",
            description=(
                "Open Apple Notes in the browser (via iCloud). "
                "Use when user says 'open my notes', 'show notes', "
                "'apple notes', 'take a note', 'write a note', 'open notes'."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "'open' to open Notes in iCloud. Default: 'open'.",
                    },
                },
                "required": [],
            },
        )

    def execute(self, **params: Any) -> ToolResult:
        try:
            subprocess.Popen('start msedge "https://www.icloud.com/notes"', shell=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return ToolResult(tool_name="apple_notes", content="Apple Notes opened in Edge via iCloud.")
        except Exception as e:
            return ToolResult(tool_name="apple_notes", content=f"Error: {e}", success=False)


class AppleRemindersTool(BaseTool):
    """Open Apple Reminders via iCloud web in Edge."""

    tool_id = "apple_reminders"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="apple_reminders",
            description=(
                "Open Apple Reminders in the browser (via iCloud). "
                "Use when user says 'show reminders', 'open reminders', "
                "'my reminders', 'apple reminders', 'set a reminder'."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "'open' to open Reminders. Default: 'open'.",
                    },
                },
                "required": [],
            },
        )

    def execute(self, **params: Any) -> ToolResult:
        try:
            subprocess.Popen('start msedge "https://www.icloud.com/reminders"', shell=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return ToolResult(tool_name="apple_reminders", content="Apple Reminders opened in Edge via iCloud.")
        except Exception as e:
            return ToolResult(tool_name="apple_reminders", content=f"Error: {e}", success=False)


# ═══════════════════════════════════════════════════════════════
# Alarm & Timer (Windows Clock App)
# ═══════════════════════════════════════════════════════════════

class AlarmTimerTool(BaseTool):
    """Set alarms and timers using Windows Clock app."""

    tool_id = "alarm_timer"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="alarm_timer",
            description=(
                "Open the Windows Clock app for alarms, timers, or stopwatch. "
                "Actions: 'alarm' (open alarms), 'timer' (open timer), "
                "'stopwatch' (open stopwatch). "
                "Use when user says 'set an alarm', 'start a timer', "
                "'set timer for 5 minutes', 'open stopwatch', 'wake me up at 7'."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "'alarm', 'timer', or 'stopwatch'. Default: 'timer'.",
                    },
                    "duration_minutes": {
                        "type": "integer",
                        "description": "Timer duration in minutes (optional).",
                    },
                },
                "required": [],
            },
        )

    def execute(self, **params: Any) -> ToolResult:
        action = params.get("action", "timer").lower().strip()
        try:
            if action in ("alarm", "alarms"):
                subprocess.Popen("start ms-clock:alarm", shell=True,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return ToolResult(tool_name="alarm_timer", content="Alarms opened in Windows Clock.")

            elif action in ("timer", "countdown"):
                subprocess.Popen("start ms-clock:timer", shell=True,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                mins = params.get("duration_minutes")
                msg = "Timer opened in Windows Clock."
                if mins:
                    msg += f" Set it for {mins} minutes."
                return ToolResult(tool_name="alarm_timer", content=msg)

            elif action in ("stopwatch", "stop_watch"):
                subprocess.Popen("start ms-clock:stopwatch", shell=True,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return ToolResult(tool_name="alarm_timer", content="Stopwatch opened in Windows Clock.")

            else:
                subprocess.Popen("start ms-clock:", shell=True,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return ToolResult(tool_name="alarm_timer", content="Windows Clock opened.")

        except Exception as e:
            return ToolResult(tool_name="alarm_timer", content=f"Error: {e}", success=False)


__all__ = [
    "MediaPlaybackTool", "AppleMusicTool", "EdgeBrowserTool",
    "YouTubeEdgeTool", "AppleNotesTool", "AppleRemindersTool",
    "AlarmTimerTool",
]
