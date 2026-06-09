# 🎙️ Real-Time AI Interview Assistant

A locally-running Python app that **listens to your microphone**, transcribes what's being said, and answers with a **local LLM via Ollama** — completely offline, no API keys needed.

---

## ✨ Features

- 🎙️ **Real-time speech recognition** — captures microphone input continuously
- 🤖 **Local LLM answers** via Ollama (Llama 3.2, Mistral, Gemma, etc.)
- 💬 **Conversation memory** — the assistant remembers context across questions
- 🎨 **Colour-coded terminal UI** — easy to read during an interview
- 🖊️ **Text mode** — type questions instead of speaking (for testing)
- 🔒 **100% local / offline** — your questions never leave your machine

---

## 🛠️ Setup

### 1. Install Ollama

Download from **https://ollama.com** and start it:

```bash
ollama serve          # starts the Ollama server
ollama pull llama3.2  # download a model (one-time)
```

Other good models to try:
```bash
ollama pull mistral
ollama pull gemma3
ollama pull phi4
```

### 2. Install Python dependencies

```bash
# macOS / Linux — needs portaudio for microphone support
# macOS:
brew install portaudio
# Ubuntu/Debian:
sudo apt install portaudio19-dev

pip install -r requirements.txt
```

### 3. Run

```bash
# 🖥️  GUI mode (recommended)
python gui.py

# Voice mode (terminal)
python assistant.py
python assistant.py --model mistral

# Text mode (type questions — no mic needed)
python text_assistant.py
```

---

## 🎤 How It Works

```
Microphone input
     │
     ▼
Google Speech Recognition (free, no key needed)
     │  transcribes speech → text
     ▼
Ollama local LLM  (llama3.2 / mistral / etc.)
     │  streams answer back
     ▼
Coloured terminal output  ✅
```

---

## 🗣️ Supported Question Types

| Type | Example |
|------|---------|
| **Coding** | "How do I reverse a linked list in Python?" |
| **System Design** | "Design a URL shortener like bit.ly" |
| **Behavioural** | "Tell me about a time you handled a conflict at work" |
| **General** | "What is the difference between REST and GraphQL?" |

---

## ⚙️ Configuration

Edit the constants at the top of `assistant.py`:

| Constant | Default | Description |
|----------|---------|-------------|
| `DEFAULT_MODEL` | `llama3.2` | Ollama model |
| `DEFAULT_LANG` | `en-US` | Speech recognition language |
| `ENERGY_THRESHOLD` | `300` | Mic sensitivity (raise if noisy) |
| `PAUSE_THRESHOLD` | `1.5` | Seconds of silence to end phrase |
| `PHRASE_LIMIT` | `30` | Max seconds per spoken phrase |

---

## 📋 Requirements

- Python 3.10+
- Ollama running locally
- A microphone (for voice mode)
- Internet connection (only for speech recognition; LLM is offline)

---

## 💡 Tips

- Speak **clearly and at a normal pace** for best transcription
- If the mic is too sensitive/not sensitive enough, adjust `ENERGY_THRESHOLD`
- Use `text_assistant.py` to test the LLM answers without a mic
- Say **"exit"** or press **Ctrl+C** to quit
- The assistant keeps conversation context — you can ask follow-up questions

---

## 🗂️ Project Structure

```
ai-interview-assistant/
├── gui.py              # 🖥️  GUI app (recommended entry point)
├── assistant.py        # Terminal voice mode
├── text_assistant.py   # Terminal text mode (for testing)
├── requirements.txt    # Python dependencies
└── README.md
```
