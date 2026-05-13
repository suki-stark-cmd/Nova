"""Windows system control tools for Nova AI.

Provides voice-controlled access to:
  - Volume (up/down/mute/set level)
  - Brightness (up/down/set level)
  - App launcher (open any app by name)
  - Screenshot
  - Lock screen
  - Wi-Fi toggle
  - Bluetooth toggle
  - Night light toggle
  - Notification center
  - Task manager
  - Clipboard
  - Window management (minimize all, snap, switch)
"""

from __future__ import annotations
import ctypes
import os
import subprocess
from typing import Any

from tools.base import BaseTool
from core.types import ToolResult, ToolSpec


# ═══════════════════════════════════════════════════════════════
# Volume Control
# ═══════════════════════════════════════════════════════════════

class VolumeControlTool(BaseTool):
    """Control system volume — up, down, mute, unmute, set level."""

    tool_id = "volume_control"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="volume_control",
            description=(
                "Control the system volume. Actions: "
                "'up' (increase by step), 'down' (decrease by step), "
                "'mute' (toggle mute), 'set' (set to a specific level 0-100). "
                "Use when user says things like 'turn up the volume', 'make it louder', "
                "'reduce volume', 'set volume to 50', 'mute the sound', 'unmute'."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action: 'up', 'down', 'mute', or 'set'.",
                    },
                    "level": {
                        "type": "integer",
                        "description": "Volume level 0-100 (only for 'set' action).",
                    },
                },
                "required": ["action"],
            },
        )

    def execute(self, **params: Any) -> ToolResult:
        action = params.get("action", "").lower().strip()
        level = params.get("level")
        
        # If only level provided, assume "set" action
        if not action and level:
            action = "set"

        try:
            if action in ("up", "increase", "louder"):
                # Send volume up key 5 times (~10% increase)
                ps = (
                    "$wshell = New-Object -ComObject WScript.Shell; "
                    "1..5 | ForEach-Object { $wshell.SendKeys([char]175) }"
                )
                subprocess.run(["powershell", "-Command", ps],
                               capture_output=True, timeout=5)
                return ToolResult(tool_name="volume_control",
                                  content="Volume increased.")

            elif action in ("down", "decrease", "lower", "quieter"):
                ps = (
                    "$wshell = New-Object -ComObject WScript.Shell; "
                    "1..5 | ForEach-Object { $wshell.SendKeys([char]174) }"
                )
                subprocess.run(["powershell", "-Command", ps],
                               capture_output=True, timeout=5)
                return ToolResult(tool_name="volume_control",
                                  content="Volume decreased.")

            elif action in ("mute", "unmute", "toggle_mute"):
                ps = (
                    "$wshell = New-Object -ComObject WScript.Shell; "
                    "$wshell.SendKeys([char]173)"
                )
                subprocess.run(["powershell", "-Command", ps],
                               capture_output=True, timeout=5)
                return ToolResult(tool_name="volume_control",
                                  content="Volume mute toggled.")

            elif action == "set" and level:
                level = max(0, min(100, int(level)))
                ps_simple = f"""
                $vol = {level} / 100.0
                $obj = New-Object -ComObject WScript.Shell
                1..50 | ForEach-Object {{ $obj.SendKeys([char]174) }}
                Start-Sleep -Milliseconds 200
                $steps = [math]::Round({level} / 2)
                1..$steps | ForEach-Object {{ $obj.SendKeys([char]175) }}
                """
                subprocess.run(["powershell", "-Command", ps_simple],
                               capture_output=True, timeout=15)
                return ToolResult(tool_name="volume_control",
                                  content=f"Volume set to {level}%.")

            else:
                return ToolResult(tool_name="volume_control",
                                  content=f"Please say 'louder', 'quieter', 'mute', or 'set volume to [0-100]'.",
                                  success=False)

        except Exception as e:
            return ToolResult(tool_name="volume_control",
                              content=f"Volume adjustment failed.", success=False)


# ═══════════════════════════════════════════════════════════════
# Brightness Control
# ═══════════════════════════════════════════════════════════════

class BrightnessControlTool(BaseTool):
    """Control screen brightness on laptop."""

    tool_id = "brightness_control"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="brightness_control",
            description=(
                "Control the screen brightness. Actions: "
                "'up' (increase), 'down' (decrease), 'set' (set to specific level 0-100). "
                "Use when user says 'increase brightness', 'dim the screen', "
                "'make it brighter', 'set brightness to 70'."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action: 'up', 'down', or 'set'.",
                    },
                    "level": {
                        "type": "integer",
                        "description": "Brightness level 0-100 (for 'set' action).",
                    },
                },
                "required": ["action"],
            },
        )

    def execute(self, **params: Any) -> ToolResult:
        action = params.get("action", "").lower().strip()
        level = params.get("level")
        
        # If only level provided, assume "set" action
        if not action and level:
            action = "set"
        
        try:
            if action in ("up", "increase", "brighter"):
                ps = """
                $current = (Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightness).CurrentBrightness
                $new = [math]::Min(100, $current + 15)
                (Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods).WmiSetBrightness(1, $new)
                Write-Output "Brightness: $new%"
                """
                r = subprocess.run(["powershell", "-Command", ps],
                                   capture_output=True, text=True, timeout=10)
                return ToolResult(tool_name="brightness_control",
                                  content=f"Brightness increased.")

            elif action in ("down", "decrease", "dimmer", "dim"):
                ps = """
                $current = (Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightness).CurrentBrightness
                $new = [math]::Max(5, $current - 15)
                (Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods).WmiSetBrightness(1, $new)
                Write-Output "Brightness: $new%"
                """
                r = subprocess.run(["powershell", "-Command", ps],
                                   capture_output=True, text=True, timeout=10)
                return ToolResult(tool_name="brightness_control",
                                  content=f"Brightness decreased.")

            elif action == "set" and level:
                level = max(5, min(100, int(level)))
                ps = f"""
                (Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods).WmiSetBrightness(1, {level})
                Write-Output "Brightness set to {level}%"
                """
                r = subprocess.run(["powershell", "-Command", ps],
                                   capture_output=True, text=True, timeout=10)
                return ToolResult(tool_name="brightness_control",
                                  content=f"Brightness set to {level}%.")

            else:
                return ToolResult(tool_name="brightness_control",
                                  content=f"Please say 'brighter', 'dimmer', or 'set brightness to [0-100]'.",
                                  success=False)
        except Exception as e:
            return ToolResult(tool_name="brightness_control",
                              content=f"Brightness adjustment failed.", success=False)


# ═══════════════════════════════════════════════════════════════
# App Launcher
# ═══════════════════════════════════════════════════════════════

# Common Windows apps → executable paths or shell commands
_APP_MAP = {
    # Browsers
    "edge": "start msedge",
    "microsoft edge": "start msedge",
    "browser": "start msedge",
    # System tools
    "settings": "start ms-settings:",
    "control panel": "control",
    "task manager": "taskmgr",
    "calculator": "calc",
    "notepad": "notepad",
    "paint": "mspaint",
    "file explorer": "explorer",
    "explorer": "explorer",
    "terminal": "wt",
    "powershell": "powershell",
    "cmd": "cmd",
    "snipping tool": "snippingtool",
    "snip": "snippingtool",
    # Microsoft Store apps
    "apple music": "start shell:AppsFolder\\AppleInc.AppleMusic_nzyj5cx40ttqa!App",
    "apple tv": "start shell:AppsFolder\\AppleInc.AppleTV_nzyj5cx40ttqa!App",
    "apple devices": "start shell:AppsFolder\\AppleInc.AppleDevices_nzyj5cx40ttqa!App",
    "icloud": "start shell:AppsFolder\\AppleInc.iCloud_nzyj5cx40ttqa!App",
    # Communication
    "whatsapp": "start shell:AppsFolder\\5319275A.WhatsAppDesktop_cv1g1gnamwfma!App",
    "telegram": "start shell:AppsFolder\\TelegramMessengerLLC.TelegramDesktop_t4vj0pshhgkwm!App",
    "discord": "start discord:",
    "teams": "start msteams:",
    # Entertainment
    "spotify": "start spotify:",
    "movies": "start mswindowsvideo:",
    "photos": "start ms-photos:",
    "camera": "start microsoft.windows.camera:",
    # Productivity
    "word": "start winword",
    "excel": "start excel",
    "powerpoint": "start powerpnt",
    "outlook": "start outlook",
    "onenote": "start onenote:",
    # Developer
    "vs code": "code",
    "vscode": "code",
    "visual studio code": "code",
}


class AppLauncherTool(BaseTool):
    """Open any Windows application by name."""

    tool_id = "open_app"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="open_app",
            description=(
                "Open a Windows application by name. "
                "Supports: Edge, Settings, Calculator, Notepad, Paint, "
                "File Explorer, Terminal, Apple Music, WhatsApp, VS Code, etc. "
                "Use when user says 'open calculator', 'launch edge', "
                "'start file explorer', 'open settings'."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "Name of the application to open.",
                    },
                },
                "required": ["app_name"],
            },
        )

    def execute(self, **params: Any) -> ToolResult:
        app = params.get("app_name", "").lower().strip()
        if not app:
            return ToolResult(tool_name="open_app", content="Please tell me which app to open.", success=False)

        # Try direct match
        cmd = _APP_MAP.get(app)
        if not cmd:
            # Fuzzy: check if any key contains the app name
            for key, val in _APP_MAP.items():
                if app in key or key in app:
                    cmd = val
                    break
        if cmd:
            try:
                subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                # Clean app name for response
                clean_name = app.replace("_", " ").title()
                return ToolResult(tool_name="open_app", content=f"Opened {clean_name}.")
            except Exception as e:
                return ToolResult(tool_name="open_app", content=f"Failed to open {app}.", success=False)

        # Try generic start command
        try:
            subprocess.Popen(f"start {app}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return ToolResult(tool_name="open_app", content=f"Trying to open {app}.")
        except Exception as e:
            return ToolResult(tool_name="open_app", content=f"I don't have that app or it's not installed.", success=False)


# ═══════════════════════════════════════════════════════════════
# Screenshot
# ═══════════════════════════════════════════════════════════════

class ScreenshotTool(BaseTool):
    """Take a screenshot and save it."""

    tool_id = "screenshot"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="screenshot",
            description=(
                "Take a screenshot and save it to the Desktop. "
                "Use when user says 'take a screenshot', 'capture screen', 'screenshot'."
            ),
            parameters={"type": "object", "properties": {}, "required": []},
        )

    def execute(self, **params: Any) -> ToolResult:
        try:
            import datetime as dt
            ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            filepath = os.path.join(desktop, f"screenshot_{ts}.png")
            ps = f"""
            Add-Type -AssemblyName System.Windows.Forms
            $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
            $bitmap = New-Object System.Drawing.Bitmap($screen.Width, $screen.Height)
            $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
            $graphics.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
            $bitmap.Save('{filepath}')
            $graphics.Dispose()
            $bitmap.Dispose()
            """
            subprocess.run(["powershell", "-Command", ps], capture_output=True, timeout=10)
            return ToolResult(tool_name="screenshot", content=f"Screenshot saved.")
        except Exception as e:
            return ToolResult(tool_name="screenshot", content=f"Failed to take screenshot.", success=False)


# ═══════════════════════════════════════════════════════════════
# Lock Screen
# ═══════════════════════════════════════════════════════════════

class LockScreenTool(BaseTool):
    """Lock the Windows screen."""

    tool_id = "lock_screen"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="lock_screen",
            description=(
                "Lock the Windows screen immediately. "
                "Use when user says 'lock my computer', 'lock screen', "
                "'lock my PC', 'lock the laptop'."
            ),
            parameters={"type": "object", "properties": {}, "required": []},
        )

    def execute(self, **params: Any) -> ToolResult:
        try:
            ctypes.windll.user32.LockWorkStation()
            return ToolResult(tool_name="lock_screen", content="Screen locked.")
        except Exception as e:
            return ToolResult(tool_name="lock_screen", content=f"Error: {e}", success=False)


# ═══════════════════════════════════════════════════════════════
# Wi-Fi Toggle
# ═══════════════════════════════════════════════════════════════

class WifiToggleTool(BaseTool):
    """Toggle Wi-Fi on or off."""

    tool_id = "wifi_toggle"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="wifi_toggle",
            description=(
                "Turn Wi-Fi on or off. "
                "Use when user says 'turn on wifi', 'disable wifi', "
                "'connect to internet', 'disconnect wifi'."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "state": {
                        "type": "string",
                        "description": "'on' to enable or 'off' to disable Wi-Fi.",
                    },
                },
                "required": ["state"],
            },
        )

    def execute(self, **params: Any) -> ToolResult:
        state = params.get("state", "on").lower()
        try:
            if state in ("on", "enable", "connect"):
                cmd = 'netsh interface set interface "Wi-Fi" admin=enable'
            else:
                cmd = 'netsh interface set interface "Wi-Fi" admin=disable'
            subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
            return ToolResult(tool_name="wifi_toggle", content=f"Wi-Fi turned {state}.")
        except Exception as e:
            return ToolResult(tool_name="wifi_toggle", content=f"Error: {e}", success=False)


# ═══════════════════════════════════════════════════════════════
# System Info
# ═══════════════════════════════════════════════════════════════

class SystemInfoTool(BaseTool):
    """Get system information — battery, CPU, memory, disk, IP."""

    tool_id = "system_info"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="system_info",
            description=(
                "Get system information like battery level, CPU usage, memory usage, "
                "disk space, IP address, or Wi-Fi status. "
                "Use when user asks 'what's my battery', 'how much disk space', "
                "'what's my IP', 'system info', 'check memory usage'."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "info_type": {
                        "type": "string",
                        "description": "Type: 'battery', 'cpu', 'memory', 'disk', 'ip', 'wifi', or 'all'.",
                    },
                },
                "required": ["info_type"],
            },
        )

    def execute(self, **params: Any) -> ToolResult:
        raw_type = params.get("info_type", "all").lower().strip()
        # Normalize fuzzy input from the LLM
        info_type = raw_type
        if "batt" in raw_type:
            info_type = "battery"
        elif "cpu" in raw_type or "processor" in raw_type:
            info_type = "cpu"
        elif "mem" in raw_type or "ram" in raw_type:
            info_type = "memory"
        elif "disk" in raw_type or "storage" in raw_type or "space" in raw_type or "drive" in raw_type:
            info_type = "disk"
        elif "ip" in raw_type or "network" in raw_type or "address" in raw_type:
            info_type = "ip"
        elif "wifi" in raw_type or "wi-fi" in raw_type or "wireless" in raw_type:
            info_type = "wifi"
        results = []
        try:
            if info_type in ("battery", "all"):
                ps = "(Get-CimInstance Win32_Battery | Select-Object -First 1).EstimatedChargeRemaining"
                r = subprocess.run(["powershell", "-Command", ps],
                                   capture_output=True, text=True, timeout=10)
                battery = r.stdout.strip() or "N/A"
                results.append(f"Battery: {battery}%")

            if info_type in ("cpu", "all"):
                ps = "(Get-CimInstance Win32_Processor).LoadPercentage"
                r = subprocess.run(["powershell", "-Command", ps],
                                   capture_output=True, text=True, timeout=10)
                results.append(f"CPU: {r.stdout.strip() or 'N/A'}%")

            if info_type in ("memory", "ram", "all"):
                ps = """
                $os = Get-CimInstance Win32_OperatingSystem
                $used = [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / 1MB, 1)
                $total = [math]::Round($os.TotalVisibleMemorySize / 1MB, 1)
                Write-Output "$used GB / $total GB"
                """
                r = subprocess.run(["powershell", "-Command", ps],
                                   capture_output=True, text=True, timeout=10)
                results.append(f"RAM: {r.stdout.strip()}")

            if info_type in ("disk", "storage", "all"):
                ps = """
                $d = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
                $free = [math]::Round($d.FreeSpace / 1GB, 1)
                $total = [math]::Round($d.Size / 1GB, 1)
                Write-Output "$free GB free / $total GB total"
                """
                r = subprocess.run(["powershell", "-Command", ps],
                                   capture_output=True, text=True, timeout=10)
                results.append(f"Disk C: {r.stdout.strip()}")

            if info_type in ("ip", "network", "all"):
                ps = "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -ne '127.0.0.1' } | Select-Object -First 1).IPAddress"
                r = subprocess.run(["powershell", "-Command", ps],
                                   capture_output=True, text=True, timeout=10)
                results.append(f"IP: {r.stdout.strip()}")

            if info_type in ("wifi", "all"):
                ps = "(netsh wlan show interfaces) -match '\\s+SSID' | Select-Object -First 1"
                r = subprocess.run(["powershell", "-Command", ps],
                                   capture_output=True, text=True, timeout=10)
                results.append(f"WiFi: {r.stdout.strip()}")

            if not results:
                return ToolResult(tool_name="system_info",
                                  content=f"Unknown type: {info_type}. Use battery/cpu/memory/disk/ip/wifi/all.",
                                  success=False)

            return ToolResult(tool_name="system_info", content="\n".join(results))

        except Exception as e:
            return ToolResult(tool_name="system_info", content=f"Error: {e}", success=False)


# ═══════════════════════════════════════════════════════════════
# Window Management
# ═══════════════════════════════════════════════════════════════

class WindowManageTool(BaseTool):
    """Manage desktop windows — minimize, maximize, switch."""

    tool_id = "window_manage"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="window_manage",
            description=(
                "Manage windows: minimize all, show desktop, switch window (Alt+Tab). "
                "Use when user says 'minimize all windows', 'show desktop', "
                "'switch window', 'go to desktop'."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "'minimize_all', 'show_desktop', 'switch', or 'close'.",
                    },
                },
                "required": ["action"],
            },
        )

    def execute(self, **params: Any) -> ToolResult:
        action = params.get("action", "").lower().strip()
        try:
            if action in ("minimize_all", "minimize", "show_desktop", "desktop"):
                ps = '(New-Object -ComObject Shell.Application).MinimizeAll()'
                subprocess.run(["powershell", "-Command", ps], capture_output=True, timeout=5)
                return ToolResult(tool_name="window_manage", content="All windows minimized. Showing desktop.")

            elif action in ("switch", "alt_tab", "next_window"):
                ps = '(New-Object -ComObject WScript.Shell).SendKeys("%{TAB}")'
                subprocess.run(["powershell", "-Command", ps], capture_output=True, timeout=5)
                return ToolResult(tool_name="window_manage", content="Switched to next window.")

            elif action in ("close", "close_window"):
                ps = '(New-Object -ComObject WScript.Shell).SendKeys("%{F4}")'
                subprocess.run(["powershell", "-Command", ps], capture_output=True, timeout=5)
                return ToolResult(tool_name="window_manage", content="Current window closed.")

            else:
                return ToolResult(tool_name="window_manage",
                                  content=f"Unknown: {action}", success=False)
        except Exception as e:
            return ToolResult(tool_name="window_manage", content=f"Error: {e}", success=False)


__all__ = [
    "VolumeControlTool", "BrightnessControlTool", "AppLauncherTool",
    "ScreenshotTool", "LockScreenTool", "WifiToggleTool",
    "SystemInfoTool", "WindowManageTool",
]
