"""
Text-Mode Interview Assistant
------------------------------
Same as assistant.py but you TYPE your questions instead of speaking.
Useful for testing without a microphone, or running in CI environments.

Usage:
  python text_assistant.py
  python text_assistant.py --model mistral
"""

import argparse
import sys
import datetime
import ollama
from colorama import Fore, Style, init as colorama_init

colorama_init(autoreset=True)

DEFAULT_MODEL = "llama3.2"

SYSTEM_PROMPT = """You are an expert technical interview assistant.
When the user asks a question (coding, system design, behavioural, or general),
give a clear, concise answer — no longer than needed.
For coding questions: show working code and a short explanation.
For system design: use bullet points or numbered steps.
For behavioural questions: use the STAR format (Situation, Task, Action, Result).
Always be direct and interview-ready."""


def ts():
    return datetime.datetime.now().strftime("%H:%M:%S")

def banner():
    print(Fore.CYAN + Style.BRIGHT + """
╔══════════════════════════════════════════════════════╗
║      🖊️  AI Interview Assistant  —  Text Mode         ║
║     Powered by Ollama (local LLM)                    ║
╚══════════════════════════════════════════════════════╝
""")

def check_ollama(model: str):
    try:
        models = ollama.list()
        available = [m.model for m in models.models]
        match = any(model in m for m in available)
        if not match:
            print(Fore.RED + f"[!] Model '{model}' not found.")
            print(Fore.YELLOW + f"    Run:  ollama pull {model}")
            print(Fore.YELLOW + f"    Available: {available}")
            sys.exit(1)
        print(Fore.CYAN + f"[{ts()}] ✓ Ollama ready — model: {model}\n")
    except Exception as e:
        print(Fore.RED + f"[!] Cannot reach Ollama: {e}")
        print(Fore.YELLOW + "    Start Ollama first:  ollama serve")
        sys.exit(1)


def ask_llm(question: str, model: str, history: list) -> str:
    history.append({"role": "user", "content": question})
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    print(f"\n{Fore.GREEN}[{ts()}] 🤖  AI:\n{Style.RESET_ALL}", end="", flush=True)
    full_reply = ""
    try:
        for chunk in ollama.chat(model=model, messages=messages, stream=True):
            text = chunk.message.content
            print(Fore.GREEN + text, end="", flush=True)
            full_reply += text
    except Exception as e:
        full_reply = f"[Error: {e}]"
        print(Fore.RED + full_reply)

    print()
    history.append({"role": "assistant", "content": full_reply})
    return full_reply


def run(model: str):
    banner()
    check_ollama(model)
    print(Fore.CYAN + "Type your interview question below. Type 'exit' to quit.\n")
    print(Fore.BLUE + "─" * 60)

    history = []
    while True:
        try:
            question = input(Fore.YELLOW + f"[{ts()}] 🎙  YOU: " + Style.RESET_ALL).strip()
        except (EOFError, KeyboardInterrupt):
            print("\n" + Fore.CYAN + "Bye! Good luck 🚀")
            break

        if not question:
            continue
        if question.lower() in {"exit", "quit", "bye", "stop"}:
            print(Fore.CYAN + "Bye! Good luck 🚀")
            break

        print(Fore.BLUE + "─" * 60)
        ask_llm(question, model, history)
        print(Fore.BLUE + "─" * 60)


def main():
    parser = argparse.ArgumentParser(description="Text-mode AI Interview Assistant")
    parser.add_argument("--model", "-m", default=DEFAULT_MODEL,
                        help=f"Ollama model  (default: {DEFAULT_MODEL})")
    args = parser.parse_args()
    run(model=args.model)


if __name__ == "__main__":
    main()
