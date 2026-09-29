"""
Indian Railways — Live data via Gemini grounded search.

Fetches train status, seat availability, PNR status and train search
DIRECTLY through Gemini's Google Search grounding — no browser opens,
no external API key needed, no website redirect.

Triggers (Hindi + English):
  "Train 12301 ka status kya hai?"
  "NDLS se PNBE kaunsi train hai?"
  "PNR 1234567890 check karo"
  "Rajdhani mein seat available hai?"
  "Train 12301 abhi kahan hai?"
  "Is there availability in 3A class in train 12302 on 5 October?"
"""

import sys
import threading
import time
from pathlib import Path

# ── Quota circuit-breaker (same pattern as web_search.py) ────────────────────
_COOLDOWN_SEC        = 600
_quota_blocked_until = 0.0
_quota_lock          = threading.Lock()


def _gemini_ok() -> bool:
    with _quota_lock:
        return time.monotonic() >= _quota_blocked_until


def _note_quota_error(exc: Exception) -> None:
    global _quota_blocked_until
    if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
        with _quota_lock:
            _quota_blocked_until = time.monotonic() + _COOLDOWN_SEC
        print("[Train] Gemini grounding quota hit — cooling down 10 min")


def _log(msg: str, player=None) -> None:
    print(f"[Train] {msg}")
    if player:
        try:
            player.write_log(f"JARVIS: {msg}")
        except Exception:
            pass


# ── Core: ask Gemini with Google Search grounding ────────────────────────────

def _gemini_grounded(query: str, timeout: int = 25) -> str | None:
    """
    Run a Gemini grounded search and return the text response.
    Returns None if Gemini is unavailable or quota is blocked.
    """
    if not _gemini_ok():
        return None
    try:
        from core import gemini
        response = gemini.call(
            query,
            tier=gemini.SEARCH,
            config={"tools": [{"google_search": {}}]},
            timeout_ms=timeout * 1000,
        )
        if response is None:
            return None
        text = ""
        for part in response.candidates[0].content.parts:
            if hasattr(part, "text") and part.text:
                text += part.text
        return text.strip() or None
    except Exception as e:
        _note_quota_error(e)
        print(f"[Train] Gemini grounded search failed: {e}")
        return None


def _ddg_search(query: str, max_results: int = 5) -> str:
    """DuckDuckGo fallback — returns plain text summary."""
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(f"• {r.get('title','')}: {r.get('body','')}")
        if results:
            return "\n".join(results)
    except Exception as e:
        print(f"[Train] DDG fallback failed: {e}")
    return ""


def _fetch(query: str, player=None) -> str:
    """
    Fetch answer via Gemini grounded search, fall back to DDG.
    Always returns a spoken-ready string — never opens a browser.
    """
    # Try Gemini first
    result = _gemini_grounded(query)
    if result:
        print(f"[Train] Gemini answered ({len(result)} chars)")
        return result

    # Fall back to DDG text search
    print("[Train] Gemini unavailable — trying DDG")
    ddg = _ddg_search(query)
    if ddg:
        return ddg

    return "Sir, I could not fetch live train data right now. The search service is temporarily unavailable. Please try again in a moment."


# ── Date helpers ─────────────────────────────────────────────────────────────

import datetime

def _readable_date(date_str: str) -> str:
    """Convert user date hint to a readable string for the search query."""
    today = datetime.date.today()
    s = (date_str or "").strip().lower()
    if not s or s in ("today", "aaj", ""):
        return today.strftime("%d %B %Y")
    if s in ("tomorrow", "kal", "kl"):
        return (today + datetime.timedelta(days=1)).strftime("%d %B %Y")
    # Try ISO and common formats
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y%m%d"):
        try:
            return datetime.datetime.strptime(s, fmt).strftime("%d %B %Y")
        except ValueError:
            pass
    # Natural: "5 October", "October 5"
    for fmt in ("%d %B", "%B %d", "%d %b", "%b %d"):
        try:
            d = datetime.datetime.strptime(s, fmt).replace(year=today.year)
            if d.date() < today:
                d = d.replace(year=today.year + 1)
            return d.strftime("%d %B %Y")
        except ValueError:
            pass
    return date_str  # Return as-is if we can't parse


# ── Action handler ────────────────────────────────────────────────────────────

def train_action(parameters: dict, player=None, session_memory=None) -> str:
    action     = parameters.get("action", "search").strip().lower()
    from_stn   = parameters.get("from_station", "").strip()
    to_stn     = parameters.get("to_station", "").strip()
    date_raw   = parameters.get("date", "today")
    train_no   = parameters.get("train_number", "").strip()
    seat_class = parameters.get("class", "").strip().upper()
    pnr        = parameters.get("pnr", "").strip().replace(" ", "")
    train_name = parameters.get("train_name", "").strip()
    date_str   = _readable_date(date_raw)

    # Build a precise Gemini grounded search query
    if action == "pnr":
        if not pnr:
            return "Sir, please provide the 10-digit PNR number."
        if len(pnr) != 10 or not pnr.isdigit():
            return f"Sir, '{pnr}' doesn't look like a valid 10-digit PNR. Please check."
        query = (
            f"Indian Railways PNR status for PNR number {pnr}. "
            f"Check current booking status, seat number, train name, journey date, "
            f"from station, to station, and passenger status. "
            f"Provide exact current status from IRCTC."
        )
        _log(f"Checking PNR {pnr}", player)

    elif action == "live_status":
        train_ref = train_no or train_name
        if not train_ref:
            return "Sir, please provide the train number or name for live status."
        query = (
            f"Indian Railways live running status of train {train_ref} today {date_str}. "
            f"Where is the train right now, which station has it passed, "
            f"is it on time or delayed, how many minutes late, "
            f"expected arrival at next station. Get current live status from NTES or where is my train."
        )
        _log(f"Checking live status: {train_ref}", player)

    elif action == "availability":
        train_ref = train_no or train_name
        if not train_ref:
            return "Sir, please provide the train number or name to check seat availability."
        class_str = f"in {seat_class} class" if seat_class else ""
        route_str = f"from {from_stn} to {to_stn}" if from_stn and to_stn else ""
        query = (
            f"Indian Railways seat availability for train {train_ref} "
            f"{route_str} {class_str} on {date_str}. "
            f"How many seats are available? Is it AVAILABLE, WL (waitlist), "
            f"or REGRET? Provide current availability from IRCTC."
        )
        _log(f"Checking availability: {train_ref} {class_str} on {date_str}", player)

    elif action == "search":
        if not from_stn or not to_stn:
            return (
                "Sir, please tell me the departure and destination stations. "
                "For example: 'Find trains from Delhi to Patna on 5 October'."
            )
        query = (
            f"List all Indian Railways trains running from {from_stn} to {to_stn} on {date_str}. "
            f"For each train give: train number, train name, departure time, arrival time, "
            f"total journey duration, and days of operation. "
            f"Get current schedule data."
        )
        _log(f"Searching trains: {from_stn} → {to_stn} on {date_str}", player)

    else:
        # Generic train query fallback
        query = (
            f"Indian Railways: {action} {train_no or train_name or ''} "
            f"{from_stn} {to_stn} {date_str}. "
            f"Provide accurate current data."
        )
        _log(f"Generic train query: {action}", player)

    result = _fetch(query, player)

    # Keep it concise for voice — summarise if too long
    if len(result) > 1200:
        # Ask Gemini to summarise it for voice
        summary_q = (
            f"Summarise the following Indian Railways information in 3-4 short sentences "
            f"suitable for speaking aloud. Be specific with numbers, times and status:\n\n{result[:2000]}"
        )
        summary = _gemini_grounded(summary_q, timeout=15)
        if summary and len(summary) < len(result):
            result = summary

    return result


# ── Tool declaration ──────────────────────────────────────────────────────────

TOOL = {
    "name": "train_search",
    "description": (
        "Fetch Indian Railways data DIRECTLY — live train status, seat availability, "
        "PNR status, and trains between stations — WITHOUT opening any browser or website. "
        "Use this when the user asks (in Hindi or English): "
        "train status, train kahan hai, seat available hai kya, PNR check karo, "
        "konsi train hai X se Y, live running status, delay kitna hai, "
        "kitni seat bachi hai, ticket available hai kya. "
        "ALWAYS use this tool for any Indian Railways / IRCTC query. "
        "Do NOT use web_search for train queries — use this tool instead. "
        "This tool fetches the answer itself and speaks it — no browser opens."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": (
                    "'search'       — find trains between two stations on a date. "
                    "'availability' — check seat availability in a specific train. "
                    "'pnr'          — check PNR booking status. "
                    "'live_status'  — live running position of a train right now."
                ),
            },
            "from_station": {
                "type": "STRING",
                "description": (
                    "Departure station — full name or 3-5 letter code "
                    "(e.g. 'New Delhi' or 'NDLS', 'Patna' or 'PNBE', 'Mumbai Central' or 'BCT')."
                ),
            },
            "to_station": {
                "type": "STRING",
                "description": "Destination station — full name or code.",
            },
            "date": {
                "type": "STRING",
                "description": (
                    "Travel/journey date. Examples: 'today', 'tomorrow', '5 October', "
                    "'2024-10-05'. Defaults to today."
                ),
            },
            "train_number": {
                "type": "STRING",
                "description": "5-digit Indian Railways train number (e.g. '12301' for Howrah Rajdhani).",
            },
            "train_name": {
                "type": "STRING",
                "description": "Train name if number is unknown (e.g. 'Rajdhani Express', 'Shatabdi').",
            },
            "class": {
                "type": "STRING",
                "description": (
                    "Coach class for availability: "
                    "SL (Sleeper), 3A (AC 3-Tier), 2A (AC 2-Tier), "
                    "1A (AC First Class), CC (Chair Car), 2S (Second Sitting)."
                ),
            },
            "pnr": {
                "type": "STRING",
                "description": "10-digit PNR number for status check (digits only).",
            },
        },
        "required": [],
    },
    "handler": train_action,
}
