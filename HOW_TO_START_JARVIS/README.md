# 🤖 HOW TO START JARVIS (Mark LV)

> **Your complete step-by-step guide to running the JARVIS AI Assistant**

---

## 📋 TABLE OF CONTENTS

1. [Prerequisites](#-prerequisites)
2. [Step 1 — Get a Gemini API Key](#-step-1--get-a-gemini-api-key)
3. [Step 2 — Install Python](#-step-2--install-python)
4. [Step 3 — Clone / Download the Project](#-step-3--clone--download-the-project)
5. [Step 4 — Run Setup](#-step-4--run-setup)
6. [Step 5 — Launch JARVIS](#-step-5--launch-jarvis)
7. [First Launch — What to Expect](#-first-launch--what-to-expect)
8. [Optional — Enable "Hey Jarvis" Wake Word](#-optional--enable-hey-jarvis-wake-word)
9. [Talking to JARVIS](#-talking-to-jarvis)
10. [Troubleshooting](#-troubleshooting)
11. [Quick Reference Card](#-quick-reference-card)

---

## ✅ Prerequisites

Before you begin, make sure you have the following:

| Requirement | Minimum | Notes |
|---|---|---|
| **Operating System** | Windows 10/11, macOS, or Linux | All three are fully supported |
| **Python** | 3.11, 3.12, or 3.13 | ⚠️ Python 3.10 and below will NOT work |
| **Microphone** | Any working microphone | Required for voice commands |
| **Speakers / Headphones** | Any working audio output | Required to hear JARVIS reply |
| **Internet Connection** | Broadband recommended | Needed for Gemini Live API |
| **Gemini API Key** | Free tier is enough | See Step 1 below |

> **GPU is NOT required.** The holographic avatar and video playback are rendered entirely in software.

---

## 🔑 Step 1 — Get a Gemini API Key

JARVIS runs on Google's Gemini Live API. You need a **free API key**.

1. Go to 👉 **[https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)**
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the key — it looks like: `AIzaSy...`
5. Keep it somewhere safe (you'll paste it on first launch)

> 💡 The free tier is sufficient for normal use. No credit card required.

---

## 🐍 Step 2 — Install Python

> **Skip this step if you already have Python 3.11, 3.12, or 3.13 installed.**

### Check your current Python version:

```bash
python --version
# or
python3 --version
```

### Install Python (if needed):

| Platform | Download |
|---|---|
| **Windows** | [python.org/downloads](https://www.python.org/downloads/) — check **"Add Python to PATH"** during install |
| **macOS** | [python.org/downloads](https://www.python.org/downloads/) or `brew install python@3.12` |
| **Linux** | `sudo apt install python3.12` (Ubuntu/Debian) or `sudo dnf install python3.12` (Fedora) |

> ⚠️ **Windows users**: Make sure **"Add Python to PATH"** is checked during installation!

---

## 📁 Step 3 — Clone / Download the Project

### Option A — Using Git (Recommended)

```bash
git clone https://github.com/FatihMakes/Mark-LV.git
cd Mark-LV
```

### Option B — Download as ZIP

1. Go to the GitHub repository page
2. Click the green **"Code"** button → **"Download ZIP"**
3. Extract the ZIP file to a folder of your choice
4. Open a terminal and `cd` into that folder

---

## ⚙️ Step 4 — Run Setup

This installs all required Python packages for **your specific operating system**.

```bash
python setup.py
```

> On macOS/Linux you may need to use `python3` instead of `python`:
> ```bash
> python3 setup.py
> ```

**What setup does:**
- ✅ Checks your Python version
- ✅ Installs all Python dependencies (Windows-only packages are skipped on Mac/Linux, and vice-versa)
- ✅ Installs the Playwright browsers (Chromium + Firefox) for web automation
- ✅ Checks that the avatar face model is present

**Alternatively**, you can install dependencies manually:

```bash
pip install -r requirements.txt
python -m playwright install chromium firefox
```

> ⚠️ **If you see a `ModuleNotFoundError`**: Run `pip install <module_name>` to install it manually.

---

## 🚀 Step 5 — Launch JARVIS

```bash
python main.py
```

> On macOS/Linux:
> ```bash
> python3 main.py
> ```

---

## 🌟 First Launch — What to Expect

The **first time** you run JARVIS, a setup screen will appear:

1. **Paste your Gemini API Key** into the field provided
2. (Optional) Set your **name**, choose a **voice**, and pick a **colour theme**
3. Click **Save / Launch**

Your settings are saved to `config/api_keys.json` — you won't need to enter the key again.

### The HUD (Heads-Up Display) will show:

| Element | What it is |
|---|---|
| **Holographic Avatar** | Animated face that lip-syncs with speech |
| **Waveform Bar** | Pulses to your mic (listening) or JARVIS's voice (speaking) |
| **Activity Log** | Shows what JARVIS is doing in real time |
| **⚙ Settings Button** | Access audio devices, wake word, theme, and more |

---

## 🎤 Optional — Enable "Hey Jarvis" Wake Word

The wake word lets JARVIS listen passively and wake up when you say **"Hey Jarvis"**.

1. Open the app
2. Click **⚙** (Settings) in the HUD
3. Go to **WAKE WORD**
4. Click the download/enable button — it downloads the tiny model automatically (~few MB, fully local)

> 💡 Without the wake word, use **Ctrl+Space** (hold to talk) to speak to JARVIS.

---

## 🗣️ Talking to JARVIS

### Push-to-Talk (Default)

| Action | How |
|---|---|
| **Open mic** | Hold **Ctrl+Space** |
| **Release** | Let go of Ctrl+Space — JARVIS processes your speech |

### With Wake Word Enabled

Just say **"Hey Jarvis"** — it will wake up and listen automatically. It auto-sleeps after 2 minutes of silence.

### Example Commands to Try

```
"What time is it?"
"Open Chrome"
"Search the news for AI updates"
"Take a screenshot"
"Turn up the volume"
"What's the weather today?"
"Play the new Dune trailer"
"Remind me at 3pm to call mom"
"Open my Downloads folder"
"Who are you?"
```

---

## 🔧 Troubleshooting

### ❌ "ModuleNotFoundError: No module named 'X'"

```bash
pip install X
```

Replace `X` with the missing module name.

---

### ❌ JARVIS can't hear me / microphone not working

1. Click **⚙** → **🎧 AUDIO DEVICES**
2. Select your correct microphone from the dropdown
3. Click Save

> The list is filtered and measured — only working devices appear.

---

### ❌ JARVIS is silent / no audio output

1. Click **⚙** → **🎧 AUDIO DEVICES**
2. Select your correct speaker/headphones
3. Click Save

---

### ❌ "Python version" error

Make sure you are using Python **3.11, 3.12, or 3.13**:

```bash
python --version
```

If the wrong version runs, try:

```bash
python3.12 setup.py
python3.12 main.py
```

---

### ❌ API Key not working

- Make sure you copied the **full key** (starts with `AIzaSy...`)
- Check [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) to confirm the key is active
- Delete `config/api_keys.json` and re-launch to re-enter your key

---

### ❌ Playwright browsers failed to install

Run this manually:

```bash
python -m playwright install chromium firefox
```

> ⚠️ This downloads several hundred MB from a CDN. Everything except browser automation works without it.

---

### ❌ Wake word / "Hey Jarvis" not working

- Enable it from **⚙ → WAKE WORD** inside the app (not from the terminal)
- Make sure your microphone is selected correctly under **⚙ → AUDIO DEVICES**

---

## 📇 Quick Reference Card

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  JARVIS (Mark LV) — Quick Start
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. Get free API key → aistudio.google.com/app/apikey
  2. Install Python 3.11–3.13
  3. cd Mark-LV
  4. python setup.py          ← installs dependencies
  5. python main.py           ← launches JARVIS

  TALK:  Hold Ctrl+Space to speak
  WAKE:  Say "Hey Jarvis" (enable in ⚙ → WAKE WORD)
  SETTINGS: Click ⚙ in the HUD

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  KEY FILES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  main.py              ← Run this to start JARVIS
  setup.py             ← Run this ONCE to install deps
  config/api_keys.json ← Your API key (auto-created)
  memory/long_term.json← What JARVIS remembers about you
  plugins/             ← Drop .py files here to add skills

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 📺 More Help

- **YouTube tutorial**: [@FatihMakes](https://www.youtube.com/@FatihMakes)
- **GitHub**: The full `readme.md` in the project root has deep technical details

---

*Guide for Mark LV (55) — The Ultimate Cross-Platform Personal AI Assistant*
