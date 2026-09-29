"""
macOS Notification Reader

Strategy:
1. Open Notification Center by clicking the clock in the menu bar
2. Take a screenshot  
3. Return a special response that tells main.py to trigger screen_process
   so Gemini vision can actually SEE and READ the notifications.

Triggers:
  "notifications batao", "koi notification aayi hai kya?",
  "check notifications", "WhatsApp notifications dikhao",
  "any new messages?", "koi alert hai kya?"
"""

import subprocess
import time
import re
from config import is_mac, is_windows

try:
    import pyautogui
    _PYAUTOGUI = True
except ImportError:
    _PYAUTOGUI = False


# ── Open Notification Center ──────────────────────────────────────────────────

def _open_notification_center() -> bool:
    """Click top-right clock area to open Notification Center."""
    if not _PYAUTOGUI:
        return False
    try:
        w, h = pyautogui.size()
        # macOS: clock is at top-right. Click just left of the very corner.
        pyautogui.click(w - 60, 8)
        time.sleep(1.8)
        return True
    except Exception as e:
        print(f"[Notifications] open NC failed: {e}")
        return False


def _close_notification_center():
    try:
        if _PYAUTOGUI:
            import pyautogui as _pag
            w, h = _pag.size()
            _pag.click(w // 2, h // 2)   # click away to close NC
            time.sleep(0.4)
    except Exception:
        pass


# ── AppleScript: quick text grab ──────────────────────────────────────────────

_AS_GROUPS = '''
set out to {}
tell application "System Events"
    tell process "NotificationCenter"
        set wins to every window
        repeat with w in wins
            set gs to {}
            try
                set gs to every group of w
            end try
            repeat with g in gs
                set desc to ""
                try
                    set desc to description of g
                end try
                if desc is not "" then
                    set end of out to desc
                end if
            end repeat
        end repeat
    end tell
end tell
set AppleScript's text item delimiters to "|"
return out as string
'''

_SKIP_RE = re.compile(
    r"com\.apple\.|BatteriesAvocado|WorldClockWidget|^Featured$|"
    r"^Month$|^Notification Center$|^\d{1,2}:\d{2}",
    re.IGNORECASE,
)


def _quick_read_applescript() -> list:
    try:
        r = subprocess.run(
            ["osascript", "-e", _AS_GROUPS],
            capture_output=True, text=True, timeout=8,
        )
        raw = r.stdout.strip()
        if not raw:
            return []
        items, seen, result = raw.split("|"), set(), []
        for item in items:
            item = item.strip()
            if not item or len(item) < 3 or _SKIP_RE.search(item):
                continue
            lo = item.lower()
            if lo not in seen:
                seen.add(lo)
                result.append(item)
        return result
    except Exception as e:
        print(f"[Notifications] AppleScript error: {e}")
        return []


# ── Main logic ─────────────────────────────────────────────────────────────────

def _get_mac_notifications() -> str:
    # Step 1: Open Notification Center
    opened = _open_notification_center()

    # Step 2: Try AppleScript quick read
    items = _quick_read_applescript()
    if items:
        _close_notification_center()
        lines = [f"{i}. {n}" for i, n in enumerate(items, 1)]
        return "Current notifications:\n" + "\n".join(lines)

    # Step 3: If nothing via AppleScript, ask Jarvis to use screen_process
    # Return a special trigger that tells the AI to look at the screen
    if opened:
        # Don't close yet — let Jarvis see the NC on screen
        return (
            "[TAKE_SCREENSHOT_NOW] "
            "Notification Center is now open on screen. "
            "Call screen_process with angle='screen' and text='Read all the "
            "notification content visible in the Notification Center panel on the "
            "right side of the screen. List every app name, message preview, time, "
            "and any other text you can see in the notification panel.' "
            "Do this immediately and report what you see."
        )

    # Step 4: Total fallback
    return (
        "Sir, Notification Center could not be opened automatically. "
        "Please click the clock in the top-right corner of your screen "
        "to open it, then say 'notifications batao' again."
    )


def _get_windows_notifications() -> str:
    try:
        ps = (
            "Add-Type -AssemblyName System.Runtime.WindowsRuntime; "
            "$m=[Windows.UI.Notifications.ToastNotificationManager,"
            "Windows.UI.Notifications,ContentType=WindowsRuntime];"
            "foreach($n in $m::History.GetHistory()){$n.Content.GetXml()}"
        )
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0 and r.stdout.strip():
            texts = re.findall(r'<text[^>]*>([^<]+)</text>', r.stdout)
            if texts:
                lines = [f"{i}. {t}" for i, t in enumerate(texts[:15], 1)]
                return "Current notifications:\n" + "\n".join(lines)
    except Exception as e:
        print(f"[Notifications] Windows error: {e}")
    return "Sir, no notifications found."


# ── Action handler ─────────────────────────────────────────────────────────────

def notifications_action(parameters: dict, player=None, session_memory=None) -> str:
    action     = parameters.get("action", "read").strip().lower()
    app_filter = parameters.get("app", "").strip()

    print(f"[Notifications] action={action!r}  app={app_filter!r}")

    if action == "read":
        if is_mac():
            result = _get_mac_notifications()
        elif is_windows():
            result = _get_windows_notifications()
        else:
            return "Sir, supported on macOS and Windows only."

        if player:
            try:
                player.write_log("[Notifications] Read complete")
            except Exception:
                pass
        return result

    return f"Unknown action '{action}'. Use 'read'."


# ── Tool declaration ───────────────────────────────────────────────────────────

TOOL = {
    "name": "notifications",
    "description": (
        "Opens Notification Center and reads current macOS/Windows notifications. "
        "Use when user says (Hindi or English): "
        "'notifications batao', 'koi notification aayi hai kya?', "
        "'check notifications', 'notifications padho', "
        "'WhatsApp ke notifications batao', 'any new messages?', "
        "'kya koi message aaya hai?', 'koi alert hai kya?', "
        "'notification center mein kya hai?'. "
        "This opens Notification Center automatically, then reads it. "
        "If it returns [TAKE_SCREENSHOT_NOW], immediately call screen_process "
        "with angle='screen' to visually read the notifications."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "'read' — open and read notifications (default)",
            },
            "app": {
                "type": "STRING",
                "description": "Filter by app: 'WhatsApp', 'Mail', 'Messages'. Leave empty for all.",
            },
        },
        "required": [],
    },
    "handler": notifications_action,
}
