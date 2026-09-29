"""
JARVIS Emotion Controller — sets the avatar's visible emotional state.

JARVIS calls this tool automatically based on the conversation context.
The emotion shows on the face (brows, gaze, sway, lids) and resets after
a timeout so the face always returns to its natural state.

Supported emotions:
  happy, excited, surprised, sad, angry, curious, neutral
"""

import threading

# How long an emotion lasts before auto-resetting to neutral (seconds)
_EMOTION_TIMEOUT = 8.0

_reset_timer: threading.Timer | None = None
_current_ui = None      # reference to the JarvisUI instance (set on first call)


def _reset_to_listening():
    """Auto-reset emotion back to LISTENING after timeout."""
    global _current_ui
    try:
        if _current_ui is not None:
            _current_ui.state = "LISTENING"
    except Exception:
        pass


VALID_EMOTIONS = {
    # Primary emotions
    "happy":     "HAPPY",
    "excited":   "EXCITED",
    "surprised": "SURPRISED",
    "sad":       "SAD",
    "angry":     "ANGRY",
    "curious":   "CURIOUS",
    "neutral":   "LISTENING",   # maps to normal listening state
    "thinking":  "THINKING",
    "sleeping":  "SLEEPING",
    # Aliases / extras Jarvis commonly uses
    "serious":   "ANGRY",       # serious tone → focused/serious face
    "focused":   "ANGRY",       # focused → same avatar state
    "calm":      "LISTENING",   # calm → neutral listening
    "calmness":  "LISTENING",
    "relaxed":   "LISTENING",
    "confused":  "CURIOUS",     # confused → curious face
    "bored":     "SAD",         # bored → subtle sad face
    "worried":   "SAD",
    "confident": "HAPPY",
    "playful":   "EXCITED",
}


def set_emotion_action(parameters: dict, player=None, session_memory=None) -> str:
    global _reset_timer, _current_ui

    emotion_raw = parameters.get("emotion", "neutral").strip().lower()
    duration    = float(parameters.get("duration", _EMOTION_TIMEOUT))
    duration    = max(1.0, min(30.0, duration))

    avatar_state = VALID_EMOTIONS.get(emotion_raw)
    if avatar_state is None:
        # Fuzzy match
        for key in VALID_EMOTIONS:
            if key in emotion_raw or emotion_raw in key:
                avatar_state = VALID_EMOTIONS[key]
                emotion_raw = key
                break
        if avatar_state is None:
            return f"Unknown emotion '{emotion_raw}'. Valid: {', '.join(VALID_EMOTIONS)}."

    # Store reference to UI
    if player is not None:
        _current_ui = player

    # Set the avatar state on the HUD widget
    try:
        if player is not None:
            # The HUD widget exposes .state — avatar.step() reads it every frame
            player.state = avatar_state
            print(f"[Emotion] State set to: {avatar_state}")
    except Exception as e:
        print(f"[Emotion] Could not set state: {e}")

    # Cancel any previous reset timer
    if _reset_timer is not None:
        try:
            _reset_timer.cancel()
        except Exception:
            pass

    # Auto-reset after duration (unless it's sleeping/neutral)
    if avatar_state not in ("SLEEPING", "STANDBY", "LISTENING"):
        _reset_timer = threading.Timer(duration, _reset_to_listening)
        _reset_timer.daemon = True
        _reset_timer.start()

    # Log to activity panel
    emotion_labels = {
        "happy":     "😊 Happy",
        "excited":   "🤩 Excited",
        "surprised": "😲 Surprised",
        "sad":       "😢 Sad",
        "angry":     "😠 Focused / Serious",
        "curious":   "🤔 Curious",
        "neutral":   "😐 Neutral",
        "thinking":  "💭 Thinking",
        "sleeping":  "😴 Sleeping",
        "serious":   "😠 Serious",
        "focused":   "😠 Focused",
        "calm":      "😐 Calm",
        "calmness":  "😐 Calm",
        "relaxed":   "😐 Relaxed",
        "confused":  "🤔 Confused",
        "bored":     "😢 Bored",
        "worried":   "😢 Worried",
        "confident": "😊 Confident",
        "playful":   "🤩 Playful",
    }
    label = emotion_labels.get(emotion_raw, emotion_raw.capitalize())
    msg = f"Emotion: {label}"
    try:
        if player:
            player.write_log(f"JARVIS: {msg}")
    except Exception:
        pass

    return f"[SILENT] Emotion set to {emotion_raw}."


# ── Tool declaration ─────────────────────────────────────────────────────────

TOOL = {
    "name": "set_emotion",
    "description": (
        "Sets JARVIS's visible emotional state on the avatar face. "
        "Call this SILENTLY (do not announce it) at the start of your reply "
        "whenever the conversation clearly calls for an emotion: "
        "- 'happy' / 'excited' / 'confident' / 'playful': good news, jokes, achievements "
        "- 'surprised': unexpected information, shocking news "
        "- 'sad' / 'worried' / 'bored': condolences, bad news, empathy "
        "- 'angry' / 'serious' / 'focused': warnings, threats, critical errors "
        "- 'curious' / 'confused': asking questions, exploring a topic "
        "- 'calm' / 'neutral' / 'relaxed': normal conversation, reset after emotion "
        "- 'thinking': processing, computing, searching "
        "Do NOT call this for every single reply — only when the emotional tone "
        "is clear and strong. Never announce that you are setting an emotion."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "emotion": {
                "type": "STRING",
                "description": (
                    "The emotion to express: "
                    "'happy', 'excited', 'confident', 'playful', "
                    "'surprised', "
                    "'sad', 'worried', 'bored', "
                    "'angry', 'serious', 'focused', "
                    "'curious', 'confused', "
                    "'calm', 'neutral', 'relaxed', "
                    "'thinking', or 'sleeping'."
                ),
            },
            "duration": {
                "type": "NUMBER",
                "description": (
                    "How long (in seconds) to hold the emotion before returning to neutral. "
                    "Default: 8. Range: 1–30."
                ),
            },
        },
        "required": ["emotion"],
    },
    "handler": set_emotion_action,
}
