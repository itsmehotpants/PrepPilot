"""
Real-Time AI Interview Assistant
---------------------------------
Listens to your microphone, transcribes speech using Whisper,
and sends the question to a local Ollama LLM for instant answers.

Requirements:
  - Ollama running locally  (https://ollama.com)
  - A model pulled, e.g.:  ollama pull llama3.2
  - Python packages: see requirements.txt

Usage:
  python assistant.py
  python assistant.py --model mistral
  python assistant.py --model llama3.2 --language en
"""

import argparse
import sys
import threading
import queue
import time
import datetime

import os
import speech_recognition as sr
import ollama
from ollama import Client as OllamaClient
from colorama import Fore, Style, init as colorama_init

# Allow overriding Ollama host via env (used in Docker)
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
_client = OllamaClient(host=OLLAMA_HOST)

colorama_init(autoreset=True)

# ─────────────────────────────────────────────
# Configuration defaults
# ─────────────────────────────────────────────
DEFAULT_MODEL   = "llama3.2"
DEFAULT_LANG    = "en-US"
ENERGY_THRESHOLD = 300       # mic sensitivity; raise if too noisy
PAUSE_THRESHOLD  = 1.5       # seconds of silence to mark end of phrase
PHRASE_LIMIT     = 30        # max seconds per phrase

SYSTEM_PROMPT = """You are an expert technical interview assistant.
When the user asks a question (coding, system design, behavioural, or general),
give a clear, concise answer — no longer than needed.
For coding questions: show working code and a short explanation.
For system design: use bullet points or numbered steps.
For behavioural questions: use the STAR format (Situation, Task, Action, Result).
Always be direct and interview-ready."""


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def banner():
    print(Fore.CYAN + Style.BRIGHT + """
╔══════════════════════════════════════════════════════╗
║        🎙️  Real-Time AI Interview Assistant           ║
║     Powered by Whisper  ×  Ollama (local LLM)        ║
╚══════════════════════════════════════════════════════╝
""")

def ts():
    """Timestamp string for log lines."""
    return datetime.datetime.now().strftime("%H:%M:%S")

def print_info(msg):
    print(f"{Fore.CYAN}[{ts()}] ℹ  {msg}{Style.RESET_ALL}")

def print_user(msg):
    print(f"\n{Fore.YELLOW}[{ts()}] 🎙  YOU: {msg}{Style.RESET_ALL}")

def print_ai(label, chunk):
    """Print a streaming chunk from the LLM."""
    print(Fore.GREEN + chunk, end="", flush=True)

def print_divider():
    print(Fore.BLUE + "─" * 60)

def check_ollama(model: str):
    """Verify Ollama is running and the model is available."""
    try:
        models = _client.list()
        available = [m.model for m in models.models]
        # Allow partial match  e.g.  "llama3.2" matches "llama3.2:latest"
        match = any(model in m for m in available)
        if not match:
            print(Fore.RED + f"[!] Model '{model}' not found in Ollama.")
            print(Fore.YELLOW + f"    Run:  ollama pull {model}")
            print(Fore.YELLOW + f"    Available models: {available}")
            sys.exit(1)
        print_info(f"Ollama ✓ — using model: {model}")
    except Exception as e:
        print(Fore.RED + f"[!] Cannot reach Ollama: {e}")
        print(Fore.YELLOW + "    Make sure Ollama is running:  ollama serve")
        sys.exit(1)


# ─────────────────────────────────────────────
# LLM response (streaming)
# ─────────────────────────────────────────────

def ask_llm(question: str, model: str, history: list) -> str:
    """Stream response from Ollama; returns full answer string."""
    history.append({"role": "user", "content": question})

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    print(f"\n{Fore.GREEN}[{ts()}] 🤖  AI:\n{Style.RESET_ALL}", end="", flush=True)
    full_reply = ""
    try:
        for chunk in _client.chat(model=model, messages=messages, stream=True):
            text = chunk.message.content
            print_ai("AI", text)
            full_reply += text
    except Exception as e:
        full_reply = f"[LLM error: {e}]"
        print(Fore.RED + full_reply)

    print()  # newline after streaming ends
    history.append({"role": "assistant", "content": full_reply})
    return full_reply


# ─────────────────────────────────────────────
# Audio transcription
# ─────────────────────────────────────────────

def transcribe_audio(audio: sr.AudioData, recognizer: sr.Recognizer, language: str) -> str | None:
    """Use Google Speech Recognition (free, no key needed) to transcribe."""
    try:
        text = recognizer.recognize_google(audio, language=language)
        return text.strip()
    except sr.UnknownValueError:
        return None          # silence / unintelligible
    except sr.RequestError as e:
        print(Fore.RED + f"[!] Speech API error: {e}")
        return None


# ─────────────────────────────────────────────
# Listener thread
# ─────────────────────────────────────────────

def listen_loop(audio_queue: queue.Queue, stop_event: threading.Event,
                energy_threshold: int, pause_threshold: float):
    """Background thread — continuously captures audio phrases."""
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = energy_threshold
    recognizer.pause_threshold  = pause_threshold
    recognizer.dynamic_energy_threshold = True

    mic = sr.Microphone()
    with mic as source:
        print_info("Adjusting for ambient noise… (1 second)")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print_info("Ready — start speaking!")
        print_divider()

        while not stop_event.is_set():
            try:
                audio = recognizer.listen(source, phrase_time_limit=PHRASE_LIMIT)
                audio_queue.put(audio)
            except sr.WaitTimeoutError:
                pass
            except Exception as e:
                print(Fore.RED + f"[Listener error] {e}")


# ─────────────────────────────────────────────
# Main loop
# ─────────────────────────────────────────────

def run(model: str, language: str):
    banner()
    check_ollama(model)
    print_info(f"Speech language: {language}")
    print_info("Press  Ctrl+C  to exit\n")

    audio_queue  = queue.Queue()
    stop_event   = threading.Event()
    conversation = []   # rolling chat history sent to LLM

    recognizer = sr.Recognizer()

    # Start listener thread
    listener = threading.Thread(
        target=listen_loop,
        args=(audio_queue, stop_event, ENERGY_THRESHOLD, PAUSE_THRESHOLD),
        daemon=True,
    )
    listener.start()

    try:
        while True:
            try:
                audio = audio_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            # Transcribe
            text = transcribe_audio(audio, recognizer, language)
            if not text:
                continue

            print_user(text)
            print_divider()

            # Check for exit commands
            if text.lower() in {"exit", "quit", "stop", "bye"}:
                print_info("Bye! Good luck in your interview 🚀")
                break

            # Get LLM answer
            ask_llm(text, model, conversation)
            print_divider()

    except KeyboardInterrupt:
        print("\n")
        print_info("Stopping…")
    finally:
        stop_event.set()
        listener.join(timeout=2)
        print_info("Session ended.")


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Real-Time AI Interview Assistant (local, offline LLM via Ollama)"
    )
    parser.add_argument(
        "--model", "-m",
        default=DEFAULT_MODEL,
        help=f"Ollama model to use  (default: {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "--language", "-l",
        default=DEFAULT_LANG,
        help=f"Speech recognition language  (default: {DEFAULT_LANG})"
    )
    args = parser.parse_args()
    run(model=args.model, language=args.language)


if __name__ == "__main__":
    main()
