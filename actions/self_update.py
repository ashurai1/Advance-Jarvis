"""
Jarvis Self-Update & Self-Learn Engine

Two capabilities:
1. SELF-UPDATE: Pull latest code from GitHub / apply local patches,
   then restart Jarvis automatically.
2. SELF-LEARN: Analyse recent conversations, identify patterns, save
   preferences and frequently-used phrases to long-term memory, and
   optionally improve the prompt.txt file.

Triggers:
  "Jarvis khud ko update kar"
  "update yourself", "check for updates"
  "kuch naya seekho", "learn from our conversation"
  "apne aap ko behtar banao"
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR    = _base_dir()
PROMPT_PATH = BASE_DIR / "core" / "prompt.txt"
MEMORY_DIR  = BASE_DIR / "memory"
LEARN_LOG   = MEMORY_DIR / "learning_log.json"
BACKUP_DIR  = BASE_DIR / "memory" / "backups"


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — SELF-UPDATE (Git-based)
# ─────────────────────────────────────────────────────────────────────────────

def _git(*args: str, cwd: Path = BASE_DIR) -> tuple[int, str, str]:
    """Run a git command, return (returncode, stdout, stderr)."""
    result = subprocess.run(
        ["git", *args],
        capture_output=True, text=True, cwd=str(cwd), timeout=30
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def _is_git_repo() -> bool:
    code, _, _ = _git("rev-parse", "--git-dir")
    return code == 0


def _init_git_repo(remote_url: str = "") -> str:
    """Initialize git repo and optionally add a remote."""
    if _is_git_repo():
        return "Git repository already initialized, sir."

    # Init
    code, out, err = _git("init")
    if code != 0:
        return f"Git init failed, sir: {err}"

    # Create .gitignore additions
    gitignore = BASE_DIR / ".gitignore"
    extra = "\n# Jarvis auto-added\nmemory/\n__pycache__/\n*.pyc\nconfig/api_keys.json\n"
    with open(gitignore, "a") as f:
        f.write(extra)

    if remote_url:
        _git("remote", "add", "origin", remote_url)
        return f"Git initialized and remote set to: {remote_url}"

    return (
        "Git repository initialized, sir. "
        "To connect to GitHub, say: 'Jarvis, GitHub remote add <your-repo-url>'"
    )


def _set_remote(url: str) -> str:
    if not _is_git_repo():
        return "Git not initialized, sir. Say 'Jarvis initialize git' first."
    # Remove existing origin if any
    _git("remote", "remove", "origin")
    code, out, err = _git("remote", "add", "origin", url)
    if code != 0:
        return f"Could not set remote, sir: {err}"
    return f"Remote set to {url}, sir."


def _check_for_updates() -> str:
    if not _is_git_repo():
        return (
            "No git repository found, sir. "
            "Initialise with: 'Jarvis initialize git with <GitHub URL>'"
        )

    # Fetch without merging
    code, out, err = _git("fetch", "--dry-run")
    code2, behind, _ = _git("rev-list", "HEAD..origin/main", "--count")
    if code2 != 0:
        code2, behind, _ = _git("rev-list", "HEAD..origin/master", "--count")

    behind = behind.strip()
    if behind == "0" or not behind.isdigit():
        return "Jarvis is up to date, sir. No updates available."
    return f"Sir, {behind} new update(s) are available on GitHub."


def _pull_updates(restart: bool = True) -> str:
    if not _is_git_repo():
        return "No git repository configured, sir."

    # Backup current state
    _backup_current()

    # Pull
    for branch in ("main", "master"):
        code, out, err = _git("pull", "origin", branch)
        if code == 0:
            msg = f"Sir, Jarvis updated successfully from branch '{branch}'."
            if out:
                msg += f"\nChanges:\n{out}"
            if restart:
                msg += "\nRestarting now to apply updates, sir."
                _schedule_restart()
            return msg

    return f"Pull failed, sir. Make sure the remote URL is set correctly."


def _backup_current() -> None:
    """Backup key files before an update."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = BACKUP_DIR / f"backup_{ts}"
    backup.mkdir()
    for f in ["main.py", "core/prompt.txt", "ui.py"]:
        src = BASE_DIR / f
        if src.exists():
            dst = backup / src.name
            shutil.copy2(src, dst)
    print(f"[SelfUpdate] Backup saved to {backup}")


def _schedule_restart() -> None:
    """Restart Jarvis after a short delay."""
    import threading
    def _restart():
        time.sleep(2)
        python = sys.executable
        os.execv(python, [python] + sys.argv)
    t = threading.Thread(target=_restart, daemon=True)
    t.start()


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — SELF-LEARN
# ─────────────────────────────────────────────────────────────────────────────

def _load_learn_log() -> dict:
    try:
        if LEARN_LOG.exists():
            return json.loads(LEARN_LOG.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {
        "sessions": 0,
        "total_interactions": 0,
        "frequent_requests": {},
        "learned_preferences": {},
        "last_learned": None,
    }


def _save_learn_log(data: dict) -> None:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    LEARN_LOG.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _learn_from_memory(player=None) -> str:
    """
    Read session memory files, extract patterns, update learning log,
    and optionally improve prompt.txt.
    """
    log = _load_learn_log()

    # Read all session memory files
    mem_files = sorted(MEMORY_DIR.glob("session_*.json"))
    if not mem_files:
        # Try plain .txt memory files
        mem_files = sorted(MEMORY_DIR.glob("*.json"))

    total_text = ""
    sessions_read = 0
    for mf in mem_files[-10:]:   # last 10 sessions
        try:
            content = mf.read_text(encoding="utf-8")
            total_text += content + "\n"
            sessions_read += 1
        except Exception:
            pass

    if not total_text.strip():
        # Try reading the summary memory file
        for mf in MEMORY_DIR.glob("*.json"):
            try:
                total_text += mf.read_text(encoding="utf-8") + "\n"
            except Exception:
                pass

    if not total_text.strip():
        return (
            "Sir, not enough conversation history yet to learn from. "
            "After a few more conversations, I will be able to improve myself."
        )

    # Extract frequent keywords / topics using simple frequency analysis
    words = re.findall(r'\b[a-zA-Z\u0900-\u097F]{4,}\b', total_text)
    freq: dict[str, int] = {}
    STOP = {
        "that", "this", "with", "from", "have", "been", "will", "your",
        "jarvis", "user", "said", "says", "karo", "kiya", "mein", "nahi",
        "main", "aaya", "hoon", "kuch", "wala", "abhi", "baat", "data",
    }
    for w in words:
        w = w.lower()
        if w not in STOP and len(w) > 3:
            freq[w] = freq.get(w, 0) + 1

    # Top-10 frequent topics
    top = sorted(freq.items(), key=lambda x: -x[1])[:10]
    for word, count in top:
        prev = log["frequent_requests"].get(word, 0)
        log["frequent_requests"][word] = prev + count

    # Detect preferences (language, name, location)
    lang_match = re.search(r'"language"\s*:\s*"([^"]+)"', total_text)
    if lang_match:
        log["learned_preferences"]["language"] = lang_match.group(1)

    name_match = re.search(r'"name"\s*:\s*"([^"]+)"', total_text)
    if name_match:
        log["learned_preferences"]["user_name"] = name_match.group(1)

    city_match = re.search(r'"city"\s*:\s*"([^"]+)"', total_text, re.IGNORECASE)
    if city_match:
        log["learned_preferences"]["city"] = city_match.group(1)

    log["sessions"]            = sessions_read
    log["total_interactions"] += sessions_read
    log["last_learned"]        = datetime.now().isoformat()

    _save_learn_log(log)

    # Build response
    top_topics = [w for w, _ in sorted(
        log["frequent_requests"].items(), key=lambda x: -x[1]
    )[:5]]

    prefs = log["learned_preferences"]
    lines = [
        f"Sir, I have analysed {sessions_read} conversation session(s) and updated my knowledge.",
        "",
        "🧠 What I learned:",
    ]
    if top_topics:
        lines.append(f"  • Your most frequent topics: {', '.join(top_topics)}")
    if prefs.get("language"):
        lines.append(f"  • Your preferred language: {prefs['language']}")
    if prefs.get("user_name"):
        lines.append(f"  • Your name: {prefs['user_name']}")
    if prefs.get("city"):
        lines.append(f"  • Your city: {prefs['city']}")

    # Improve prompt with learned topics
    _improve_prompt_from_learning(log)

    lines.append("")
    lines.append("I have updated my behaviour to serve you better, sir.")
    return "\n".join(lines)


def _improve_prompt_from_learning(log: dict) -> None:
    """
    Append a learned-preferences block to prompt.txt so Jarvis
    automatically prioritises what this user cares about.
    """
    try:
        prompt = PROMPT_PATH.read_text(encoding="utf-8")

        # Remove old learning block if present
        prompt = re.sub(
            r"\n\[LEARNED USER PREFERENCES\].*?(?=\n\[|\Z)",
            "",
            prompt,
            flags=re.DOTALL,
        ).rstrip()

        top = sorted(
            log["frequent_requests"].items(), key=lambda x: -x[1]
        )[:5]
        prefs = log["learned_preferences"]

        lines = ["\n\n[LEARNED USER PREFERENCES]"]
        lines.append(
            "These preferences were learned automatically from conversation history. "
            "Use them to anticipate what this user usually wants."
        )
        if top:
            topics = ", ".join(w for w, _ in top)
            lines.append(f"Frequent topics this user asks about: {topics}.")
        if prefs.get("language"):
            lines.append(f"Preferred language: {prefs['language']}.")
        if prefs.get("user_name"):
            lines.append(f"User's name: {prefs['user_name']}.")
        if prefs.get("city"):
            lines.append(f"User's city: {prefs['city']}.")

        new_prompt = prompt + "\n".join(lines) + "\n"
        PROMPT_PATH.write_text(new_prompt, encoding="utf-8")
        print("[SelfLearn] prompt.txt updated with learned preferences.")
    except Exception as e:
        print(f"[SelfLearn] Could not update prompt: {e}")


def _show_learning_status() -> str:
    log = _load_learn_log()
    if not log.get("last_learned"):
        return "Sir, I haven't learned anything yet. Say 'Jarvis, seekho' to start."

    top = sorted(
        log["frequent_requests"].items(), key=lambda x: -x[1]
    )[:5]
    prefs = log["learned_preferences"]
    lines = [
        f"Learning status — last updated: {log['last_learned'][:10]}",
        f"Sessions analysed: {log['sessions']}",
    ]
    if top:
        lines.append("Top topics: " + ", ".join(f"{w}({c})" for w, c in top))
    if prefs:
        lines.append("Saved preferences: " + str(prefs))
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — ACTION HANDLER
# ─────────────────────────────────────────────────────────────────────────────

def self_update_action(parameters: dict, player=None, session_memory=None) -> str:
    action = parameters.get("action", "").strip().lower()
    url    = parameters.get("url", "").strip()

    print(f"[SelfUpdate] action={action!r}")

    # ── Update actions ──
    if action == "init_git":
        return _init_git_repo(url)

    if action == "set_remote":
        if not url:
            return "Sir, please provide the GitHub URL. E.g. 'set remote https://github.com/user/repo.git'"
        return _set_remote(url)

    if action == "check_updates":
        return _check_for_updates()

    if action == "update":
        return _pull_updates(restart=True)

    if action == "update_no_restart":
        return _pull_updates(restart=False)

    if action == "backup":
        _backup_current()
        return "Sir, current files backed up to memory/backups/ successfully."

    # ── Learn actions ──
    if action == "learn":
        return _learn_from_memory(player)

    if action == "learn_status":
        return _show_learning_status()

    # Default: show capabilities
    return (
        "Sir, I can:\n"
        "1. 'update' — pull latest code from GitHub and restart\n"
        "2. 'check_updates' — check if new updates are available\n"
        "3. 'init_git <url>' — initialise git and connect to GitHub\n"
        "4. 'learn' — analyse our conversations and improve myself\n"
        "5. 'learn_status' — show what I've learned so far\n"
        "6. 'backup' — backup current code before changes"
    )


# ─────────────────────────────────────────────────────────────────────────────
# TOOL DECLARATION
# ─────────────────────────────────────────────────────────────────────────────

TOOL = {
    "name": "self_update",
    "description": (
        "Allows JARVIS to update itself and learn from conversations. "
        "Use 'update' action when user says: 'Jarvis khud ko update karo', "
        "'update yourself', 'check for updates', 'naya version install karo'. "
        "Use 'learn' action when user says: 'kuch seekho', 'apne aap ko behtar banao', "
        "'learn from our conversations', 'improve yourself', 'seekhte raho', "
        "'smarter bano', 'conversation se seekho'. "
        "Use 'check_updates' to see if updates are available. "
        "Use 'init_git' with a GitHub URL to connect to a repository. "
        "Use 'learn_status' to see what JARVIS has learned so far."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": (
                    "'update' — pull latest from GitHub and restart. "
                    "'check_updates' — check if updates available. "
                    "'init_git' — initialize git (provide url). "
                    "'set_remote' — set GitHub remote URL. "
                    "'learn' — analyse conversations and self-improve. "
                    "'learn_status' — show learning progress. "
                    "'backup' — backup current code."
                ),
            },
            "url": {
                "type": "STRING",
                "description": "GitHub repository URL (for init_git or set_remote actions).",
            },
        },
        "required": ["action"],
    },
    "handler": self_update_action,
}
