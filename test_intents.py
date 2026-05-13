"""Test intent routing accuracy with varied phrasings."""
import sys
sys.path.insert(0, "d:/AI-ML/nova")
from tools.intent_router import route_intent

tests = [
    ("make it louder", "volume_control"),
    ("can you turn the volume down", "volume_control"),
    ("mute the sound please", "volume_control"),
    ("dim the screen a bit", "brightness_control"),
    ("increase the brightness", "brightness_control"),
    ("how much charge is left", "system_info"),
    ("check my battery", "system_info"),
    ("what is my disk space", "system_info"),
    ("how much RAM do I have", "system_info"),
    ("play Tamil songs on YouTube", "play_youtube"),
    ("I want to watch a video", "play_youtube"),
    ("open my notes", "apple_notes"),
    ("show my reminders", "apple_reminders"),
    ("set a timer for 10 minutes", "alarm_timer"),
    ("search for Python tutorials", "edge_browser"),
    ("open google.com", "edge_browser"),
    ("lock my computer", "lock_screen"),
    ("take a screenshot please", "screenshot"),
    ("minimize all windows", "window_manage"),
    ("show me the desktop", "window_manage"),
    ("whats the weather like", "get_weather"),
    ("what time is it", "get_time"),
    ("calculate 5 plus 3", "calculator"),
    ("next song", "media_control"),
    ("pause the music", "media_control"),
    ("play on apple music", "apple_music"),
    ("open Apple Music", "apple_music"),
    ("set an alarm for 7am", "alarm_timer"),
    ("turn on wifi", "wifi_toggle"),
    ("open file explorer", "open_app"),
]

pass_count = 0
for query, expected in tests:
    routed = route_intent(query)
    top = routed[0] if routed else "NONE"
    ok = top == expected
    pass_count += int(ok)
    mark = "PASS" if ok else "FAIL"
    extra = "" if ok else f" (got {top})"
    print(f"  [{mark}] {query:42s} -> {expected}{extra}")

print(f"\nResult: {pass_count}/{len(tests)} passed")
