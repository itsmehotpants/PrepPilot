# 🎙️ PrepPilot — Real-Time AI Interview Assistant

<div align="center">

![PrepPilot Banner](https://img.shields.io/badge/PrepPilot-AI%20Interview%20Assistant-blue?style=for-the-badge&logo=microphone)
![Python](https://img.shields.io/badge/Python-3.10%2B-green?style=for-the-badge&logo=python)
![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-orange?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Mac%20%7C%20Linux-lightgrey?style=for-the-badge)

**A fully local, offline AI assistant that listens to your interview questions in real time and answers them instantly — powered by Ollama and Whisper.**

[Features](#-features) • [Demo](#-demo) • [Installation](#-installation) • [Usage](#-usage) • [Docker](#-docker) • [FAQ](#-faq)

</div>

---

## 📌 What is PrepPilot?

PrepPilot is a desktop application that acts as your **silent co-pilot during technical interviews**. It listens to what's being said (via your microphone), transcribes the question, and uses a **locally running Large Language Model** to generate a clear, structured answer — all in real time, completely offline.

No API keys. No cloud. No data leaves your machine.

---

## ✨ Features

- 🎙️ **Real-time voice recognition** — continuously listens via your microphone
- 🤖 **Local LLM answers** — powered by Ollama (Llama 3.2, Mistral, Gemma, Phi and more)
- 💬 **Conversation memory** — remembers context across the entire session
- 🔀 **STT toggle** — switch between Google Speech Recognition (fast, needs internet) and Whisper (fully offline)
- 🎛️ **Whisper model selector** — choose from tiny / base / small / medium based on your hardware
- 🖥️ **Modern dark GUI** — built with CustomTkinter, clean and distraction-free
- 🖊️ **Text input mode** — type questions manually even while mic is active
- 📋 **One-click copy** — copy any AI answer to clipboard instantly
- 📜 **Conversation history** — sidebar shows all Q&A from the session with timestamps
- 🐳 **Docker support** — run everything with a single `docker compose up`
- 🔒 **100% local & private** — your questions never leave your machine

---

## 🎯 Supported Question Types

| Type | Example |
|------|---------|
| **Coding** | "How do I reverse a linked list in Python?" |
| **Data Structures** | "Explain the difference between a stack and a queue" |
| **System Design** | "Design a URL shortener like bit.ly" |
| **Behavioural** | "Tell me about a time you resolved a conflict at work" |
| **OS / Networks** | "What is the difference between a process and a thread?" |
| **Database** | "When would you use NoSQL over SQL?" |
| **General CS** | "What is the CAP theorem?" |

---

## 🖥️ Demo

```
╔══════════════════════════════════════════════════════╗
║        🎙️  Real-Time AI Interview Assistant           ║
║     Powered by Whisper  ×  Ollama (local LLM)        ║
╚══════════════════════════════════════════════════════╝

[10:42:01] ℹ  Ollama ✓ — using model: llama3.2
[10:42:01] ℹ  Ready — start speaking!

[10:42:15] 🎙  YOU: How do you detect a cycle in a linked list?

[10:42:15] 🤖  AI:
Use Floyd's Cycle Detection Algorithm (fast & slow pointer):

def has_cycle(head):
    slow, fast = head, head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            return True
    return False

Time complexity: O(n) | Space complexity: O(1)
The slow pointer moves 1 step, fast moves 2. If there's a cycle,
they will eventually meet.
```

---

## 🛠️ Installation

### Prerequisites

| Requirement | Link |
|-------------|------|
| Python 3.10+ | https://python.org |
| Ollama | https://ollama.com |
| PortAudio (for mic) | See below |

### Step 1 — Install Ollama & pull a model

```bash
# Download Ollama from https://ollama.com and install it
# Then pull a model (one-time download):

ollama pull llama3.2      # recommended — fast and accurate
ollama pull mistral       # alternative — great for coding
ollama pull gemma3        # Google's model — lightweight
ollama pull phi4          # Microsoft's model — very capable
```

### Step 2 — Install PortAudio (for microphone support)

**macOS:**
```bash
brew install portaudio
```

**Ubuntu / Debian:**
```bash
sudo apt install portaudio19-dev
```

**Windows:**
PortAudio is bundled with PyAudio on Windows — no separate install needed.

### Step 3 — Install Python dependencies

```bash
# Clone the repo
git clone https://github.com/itsmehotpants/PrepPilot.git
cd PrepPilot

# (Recommended) create a virtual environment
python -m venv preppilot_env
source preppilot_env/bin/activate      # Mac/Linux
preppilot_env\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt
```

---

## 🚀 Usage

### GUI Mode (Recommended)

```bash
python gui.py
```

### Terminal Voice Mode

```bash
python assistant.py                    # default model (llama3.2)
python assistant.py --model mistral    # use a different model
python assistant.py --language en-IN   # change speech language
```

### Terminal Text Mode (no mic needed)

```bash
python text_assistant.py
python text_assistant.py --model phi4
```

### Keyboard shortcuts in GUI

| Action | How |
|--------|-----|
| Submit typed question | `Enter` |
| Stop listening | Click **Stop Listening** button |
| Copy answer | Click **📋 Copy** button |
| Clear session | Click **🗑 Clear** button |

---

## 🐳 Docker

Run the entire stack (PrepPilot + Ollama) with one command — no local Python or Ollama install needed.

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### Run

```bash
# Clone the repo
git clone https://github.com/itsmehotpants/PrepPilot.git
cd PrepPilot

# Start everything (downloads llama3.2 automatically on first run)
docker compose up
```

This spins up:
- **ollama** service — local LLM server on port `11434`
- **ollama-pull** — pulls `llama3.2` automatically on first run
- **preppilot** — the interview assistant (text mode in Docker)

```bash
# Stop
docker compose down

# Rebuild after code changes
docker compose up --build

# Use a different model
# Edit docker-compose.yml → ollama-pull → change "llama3.2" to your model
```

> **Note:** The GUI requires a display and runs best natively. Docker runs the text-mode assistant.

---

## ⚙️ Configuration

Edit constants at the top of `assistant.py` or `gui.py`:

| Constant | Default | Description |
|----------|---------|-------------|
| `DEFAULT_MODEL` | `llama3.2` | Ollama model to use |
| `DEFAULT_LANG` | `en-US` | Speech recognition language |
| `ENERGY_THRESHOLD` | `300` | Mic sensitivity (raise in noisy environments) |
| `PAUSE_THRESHOLD` | `1.5` | Seconds of silence to mark end of phrase |
| `PHRASE_LIMIT` | `30` | Max seconds per spoken phrase |

**Language codes for `--language`:**

| Language | Code |
|----------|------|
| English (US) | `en-US` |
| English (India) | `en-IN` |
| English (UK) | `en-GB` |
| Hindi | `hi-IN` |

---

## 🗂️ Project Structure

```
PrepPilot/
├── gui.py                  # 🖥️  Modern GUI app (main entry point)
├── assistant.py            # 🎙️  Terminal voice mode
├── text_assistant.py       # 🖊️  Terminal text mode (for testing)
├── requirements.txt        # 📦  Python dependencies
├── Dockerfile              # 🐳  Docker image definition
├── docker-compose.yml      # 🐳  Multi-service Docker setup
├── .dockerignore           # 🐳  Docker build exclusions
└── README.md               # 📖  This file
```

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `customtkinter` | Modern dark-themed GUI |
| `SpeechRecognition` | Google STT (fast, needs internet) |
| `pyaudio` | Microphone input |
| `ollama` | Local LLM inference via Ollama |
| `faster-whisper` | Offline speech recognition |
| `colorama` | Coloured terminal output |
| `numpy` | Audio data processing |

---

## ❓ FAQ

**Q: Do I need an internet connection?**
With Google STT (default): yes, for speech recognition only. The LLM is fully offline.
With Whisper mode: completely offline — no internet needed at all.

**Q: Which Ollama model should I use?**
- `llama3.2` — best all-rounder, recommended
- `mistral` — excellent for coding questions
- `phi4` — very fast, good for quick answers
- `gemma3` — lightweight, good on low-end machines

**Q: The mic isn't picking up my voice. What do I do?**
Raise `ENERGY_THRESHOLD` in `assistant.py` (try `500` or `800`). Also check your OS microphone permissions.

**Q: Whisper mode is slow. How do I speed it up?**
Use a smaller model size — `tiny` is fastest. Switch back to Google STT if latency is a concern.

**Q: Can I use this on Mac/Linux?**
Yes — all features work on Mac and Linux. Install PortAudio first (`brew install portaudio` on Mac).

---

## 🗺️ Roadmap

- [ ] Hotkey to start/stop listening (global shortcut)
- [ ] Save session transcript to PDF
- [ ] Web version (Streamlit + Groq API)
- [ ] Custom system prompt editor in GUI
- [ ] Multi-language UI

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## 🙏 Acknowledgements

- [Ollama](https://ollama.com) — for making local LLMs easy
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — offline speech recognition
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) — modern Python GUI
- [LeetJourney](https://www.youtube.com/@LeetJourney) — original project inspiration

---

<div align="center">
Made with ❤️ by <a href="https://github.com/itsmehotpants">itsmehotpants</a>
</div>
