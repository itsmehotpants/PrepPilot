"""
AI Interview Assistant — GUI
-------------------------------
A modern desktop UI built with CustomTkinter.

Features:
  • Start / Stop listening button
  • Model selector (any Ollama model you have pulled)
  • STT mode toggle: Google Speech Recognition (fast) vs Whisper (offline)
  • Whisper model size selector (tiny → large)
  • Live transcript + AI answer panel
  • Conversation history sidebar
  • Clear / Copy buttons

Usage:
    python gui.py
"""

import threading
import queue
import time
import datetime
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

import speech_recognition as sr
import ollama

# ── appearance ────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── constants ─────────────────────────────────────────────
ENERGY_THRESHOLD = 300
PAUSE_THRESHOLD  = 1.5
PHRASE_LIMIT     = 30

WHISPER_SIZES = ["tiny", "base", "small", "medium"]   # "large" excluded — very slow on CPU

SYSTEM_PROMPT = """You are an expert technical interview assistant.
When the user asks a question (coding, system design, behavioural, or general),
give a clear, concise answer — no longer than needed.
For coding questions: show working code and a short explanation.
For system design: use bullet points or numbered steps.
For behavioural questions: use the STAR format (Situation, Task, Action, Result).
Always be direct and interview-ready."""


def ts():
    return datetime.datetime.now().strftime("%H:%M:%S")


# ══════════════════════════════════════════════════════════
#  App
# ══════════════════════════════════════════════════════════

class InterviewAssistantApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("🎙️ AI Interview Assistant")
        self.geometry("1100x750")
        self.minsize(900, 600)

        # state
        self.listening      = False
        self.stop_event     = threading.Event()
        self.audio_queue    = queue.Queue()
        self.conversation   = []          # LLM message history
        self.whisper_model  = None        # cached faster-whisper model
        self._whisper_size  = None

        self._build_ui()
        self._load_ollama_models()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── UI construction ───────────────────────────────────

    def _build_ui(self):
        # ── top bar ───────────────────────────────────────
        top = ctk.CTkFrame(self, height=56, corner_radius=0)
        top.pack(fill="x", side="top")
        top.pack_propagate(False)

        ctk.CTkLabel(top, text="🎙️  AI Interview Assistant",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=16, pady=10)

        # model selector
        ctk.CTkLabel(top, text="Model:").pack(side="left", padx=(24, 4))
        self.model_var = ctk.StringVar(value="llama3.2")
        self.model_menu = ctk.CTkOptionMenu(top, variable=self.model_var, values=["llama3.2"],
                                             width=160)
        self.model_menu.pack(side="left", padx=4)

        # STT toggle
        ctk.CTkLabel(top, text="STT:").pack(side="left", padx=(24, 4))
        self.stt_var = ctk.StringVar(value="Google")
        self.stt_menu = ctk.CTkOptionMenu(
            top, variable=self.stt_var,
            values=["Google (fast)", "Whisper (offline)"],
            width=170,
            command=self._on_stt_change,
        )
        self.stt_menu.pack(side="left", padx=4)

        # Whisper size (hidden unless Whisper selected)
        self.whisper_size_var = ctk.StringVar(value="base")
        self.whisper_size_menu = ctk.CTkOptionMenu(
            top, variable=self.whisper_size_var,
            values=WHISPER_SIZES, width=100,
        )
        # not packed yet — shown only when Whisper selected

        # start/stop button
        self.listen_btn = ctk.CTkButton(
            top, text="▶  Start Listening",
            fg_color="#2ecc71", hover_color="#27ae60",
            font=ctk.CTkFont(weight="bold"), width=160,
            command=self._toggle_listening,
        )
        self.listen_btn.pack(side="right", padx=16, pady=10)

        # clear btn
        ctk.CTkButton(top, text="🗑 Clear", width=80,
                      fg_color="transparent", border_width=1,
                      command=self._clear).pack(side="right", padx=4)

        # ── main content area ─────────────────────────────
        content = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=12, pady=(6, 6))
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=2)
        content.rowconfigure(0, weight=1)

        # ── LEFT: conversation history ─────────────────────
        left = ctk.CTkFrame(content, corner_radius=10)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        ctk.CTkLabel(left, text="Conversation History",
                     font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, pady=(10, 4), padx=10, sticky="w")

        self.history_box = ctk.CTkTextbox(left, wrap="word", state="disabled",
                                          font=ctk.CTkFont(size=12))
        self.history_box.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

        # ── RIGHT: main panel ──────────────────────────────
        right = ctk.CTkFrame(content, corner_radius=10, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(0, weight=0)
        right.rowconfigure(1, weight=1)
        right.rowconfigure(2, weight=2)
        right.columnconfigure(0, weight=1)

        # status bar
        self.status_label = ctk.CTkLabel(
            right, text="● Idle — press Start Listening",
            text_color="gray", anchor="w",
            font=ctk.CTkFont(size=13),
        )
        self.status_label.grid(row=0, column=0, sticky="ew", padx=4, pady=(0, 4))

        # transcript box
        transcript_frame = ctk.CTkFrame(right, corner_radius=10)
        transcript_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 6))
        transcript_frame.rowconfigure(1, weight=1)
        transcript_frame.columnconfigure(0, weight=1)

        ctk.CTkLabel(transcript_frame, text="🎙️  You said:",
                     font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 2))

        self.transcript_box = ctk.CTkTextbox(
            transcript_frame, wrap="word", height=90,
            font=ctk.CTkFont(size=13),
            fg_color=("#f0f0f0", "#2b2b2b"),
        )
        self.transcript_box.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

        # answer box
        answer_frame = ctk.CTkFrame(right, corner_radius=10)
        answer_frame.grid(row=2, column=0, sticky="nsew")
        answer_frame.rowconfigure(1, weight=1)
        answer_frame.columnconfigure(0, weight=1)

        ans_top = ctk.CTkFrame(answer_frame, fg_color="transparent")
        ans_top.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 2))
        ctk.CTkLabel(ans_top, text="🤖  AI Answer:",
                     font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkButton(ans_top, text="📋 Copy", width=70, height=24,
                      fg_color="transparent", border_width=1,
                      command=self._copy_answer).pack(side="right")

        self.answer_box = ctk.CTkTextbox(
            answer_frame, wrap="word",
            font=ctk.CTkFont(size=13),
            fg_color=("#f0f0f0", "#1e1e2e"),
        )
        self.answer_box.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

        # ── bottom: manual input ───────────────────────────
        bot = ctk.CTkFrame(self, height=52, corner_radius=0)
        bot.pack(fill="x", side="bottom")
        bot.pack_propagate(False)

        self.text_input = ctk.CTkEntry(bot, placeholder_text="Or type a question here…",
                                       font=ctk.CTkFont(size=13))
        self.text_input.pack(side="left", fill="x", expand=True, padx=(12, 6), pady=10)
        self.text_input.bind("<Return>", self._on_text_submit)

        ctk.CTkButton(bot, text="Send", width=80,
                      command=self._on_text_submit).pack(side="left", padx=(0, 12), pady=10)

    # ── model loading ──────────────────────────────────────

    def _load_ollama_models(self):
        def _fetch():
            try:
                models = ollama.list()
                names = [m.model for m in models.models]
                if names:
                    self.after(0, lambda: self._set_models(names))
                else:
                    self.after(0, lambda: self._set_status("⚠️  No Ollama models found — run: ollama pull llama3.2", "orange"))
            except Exception:
                self.after(0, lambda: self._set_status("⚠️  Ollama not running — start with: ollama serve", "orange"))

        threading.Thread(target=_fetch, daemon=True).start()

    def _set_models(self, names: list):
        self.model_menu.configure(values=names)
        self.model_var.set(names[0])
        self._set_status(f"● Idle — {len(names)} model(s) loaded", "gray")

    # ── STT toggle ─────────────────────────────────────────

    def _on_stt_change(self, value):
        if "Whisper" in value:
            self.whisper_size_menu.pack(in_=self.stt_menu.master, side="left", padx=4)
            self._set_status("ℹ️  Whisper mode: first use downloads model — may take a moment", "#e67e22")
        else:
            self.whisper_size_menu.pack_forget()

    def _is_whisper(self):
        return "Whisper" in self.stt_var.get()

    # ── listening control ──────────────────────────────────

    def _toggle_listening(self):
        if self.listening:
            self._stop_listening()
        else:
            self._start_listening()

    def _start_listening(self):
        self.listening  = True
        self.stop_event = threading.Event()
        self.listen_btn.configure(text="⏹  Stop Listening",
                                  fg_color="#e74c3c", hover_color="#c0392b")
        self._set_status("● Listening…", "#2ecc71")

        threading.Thread(target=self._listener_thread, daemon=True).start()
        threading.Thread(target=self._processor_thread, daemon=True).start()

    def _stop_listening(self):
        self.listening = False
        self.stop_event.set()
        self.listen_btn.configure(text="▶  Start Listening",
                                  fg_color="#2ecc71", hover_color="#27ae60")
        self._set_status("● Idle — press Start Listening", "gray")

    # ── listener thread ────────────────────────────────────

    def _listener_thread(self):
        recognizer = sr.Recognizer()
        recognizer.energy_threshold        = ENERGY_THRESHOLD
        recognizer.pause_threshold         = PAUSE_THRESHOLD
        recognizer.dynamic_energy_threshold = True

        try:
            mic = sr.Microphone()
            with mic as source:
                self.after(0, lambda: self._set_status("● Adjusting for ambient noise…", "#e67e22"))
                recognizer.adjust_for_ambient_noise(source, duration=1)
                self.after(0, lambda: self._set_status("● Listening — speak now!", "#2ecc71"))

                while not self.stop_event.is_set():
                    try:
                        audio = recognizer.listen(source, phrase_time_limit=PHRASE_LIMIT)
                        self.audio_queue.put(audio)
                    except sr.WaitTimeoutError:
                        pass
        except Exception as e:
            self.after(0, lambda: self._set_status(f"Mic error: {e}", "red"))
            self.after(0, self._stop_listening)

    # ── processor thread ───────────────────────────────────

    def _processor_thread(self):
        recognizer = sr.Recognizer()
        while not self.stop_event.is_set():
            try:
                audio = self.audio_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            self.after(0, lambda: self._set_status("● Transcribing…", "#3498db"))

            if self._is_whisper():
                text = self._transcribe_whisper(audio)
            else:
                text = self._transcribe_google(audio, recognizer)

            if not text:
                self.after(0, lambda: self._set_status("● Listening — speak now!", "#2ecc71"))
                continue

            self.after(0, lambda t=text: self._show_transcript(t))
            self.after(0, lambda: self._set_status("● Thinking…", "#9b59b6"))
            self._ask_llm(text)

    # ── transcription ──────────────────────────────────────

    def _transcribe_google(self, audio, recognizer) -> str | None:
        try:
            return recognizer.recognize_google(audio).strip()
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            self.after(0, lambda: self._set_status(f"Speech API error: {e}", "red"))
            return None

    def _transcribe_whisper(self, audio) -> str | None:
        try:
            from faster_whisper import WhisperModel
            size = self.whisper_size_var.get()

            # load / cache model
            if self.whisper_model is None or self._whisper_size != size:
                self.after(0, lambda: self._set_status(f"⏳ Loading Whisper '{size}' model…", "#e67e22"))
                self.whisper_model = WhisperModel(size, device="cpu", compute_type="int8")
                self._whisper_size = size

            import io, wave, numpy as np
            raw = audio.get_raw_data(convert_rate=16000, convert_width=2)
            audio_np = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

            segments, _ = self.whisper_model.transcribe(audio_np, language="en")
            text = " ".join(s.text for s in segments).strip()
            return text if text else None
        except Exception as e:
            self.after(0, lambda: self._set_status(f"Whisper error: {e}", "red"))
            return None

    # ── LLM ───────────────────────────────────────────────

    def _ask_llm(self, question: str):
        self.conversation.append({"role": "user", "content": question})
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + self.conversation

        self.after(0, lambda: self._clear_answer())
        full_reply = ""

        try:
            for chunk in ollama.chat(model=self.model_var.get(),
                                     messages=messages, stream=True):
                token = chunk.message.content
                full_reply += token
                self.after(0, lambda t=token: self._append_answer(t))
        except Exception as e:
            full_reply = f"[LLM error: {e}]"
            self.after(0, lambda: self._append_answer(full_reply))

        self.conversation.append({"role": "assistant", "content": full_reply})
        self.after(0, lambda q=question, a=full_reply: self._add_history(q, a))

        if self.listening:
            self.after(0, lambda: self._set_status("● Listening — speak now!", "#2ecc71"))

    # ── text input ─────────────────────────────────────────

    def _on_text_submit(self, event=None):
        text = self.text_input.get().strip()
        if not text:
            return
        self.text_input.delete(0, "end")
        self._show_transcript(text)
        self._set_status("● Thinking…", "#9b59b6")
        threading.Thread(target=self._ask_llm, args=(text,), daemon=True).start()

    # ── UI helpers ─────────────────────────────────────────

    def _set_status(self, msg: str, color: str = "gray"):
        self.status_label.configure(text=msg, text_color=color)

    def _show_transcript(self, text: str):
        self.transcript_box.configure(state="normal")
        self.transcript_box.delete("1.0", "end")
        self.transcript_box.insert("end", text)
        self.transcript_box.configure(state="disabled")

    def _clear_answer(self):
        self.answer_box.configure(state="normal")
        self.answer_box.delete("1.0", "end")
        self.answer_box.configure(state="disabled")

    def _append_answer(self, text: str):
        self.answer_box.configure(state="normal")
        self.answer_box.insert("end", text)
        self.answer_box.see("end")
        self.answer_box.configure(state="disabled")

    def _add_history(self, question: str, answer: str):
        self.history_box.configure(state="normal")
        self.history_box.insert("end", f"[{ts()}]\n")
        self.history_box.insert("end", f"Q: {question}\n", )
        self.history_box.insert("end", f"A: {answer[:120]}{'…' if len(answer)>120 else ''}\n")
        self.history_box.insert("end", "─" * 30 + "\n")
        self.history_box.see("end")
        self.history_box.configure(state="disabled")

    def _copy_answer(self):
        text = self.answer_box.get("1.0", "end").strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self._set_status("✅ Answer copied to clipboard!", "#2ecc71")
            self.after(2000, lambda: self._set_status("● Idle", "gray"))

    def _clear(self):
        self.conversation.clear()
        self._clear_answer()
        self._show_transcript("")
        self.history_box.configure(state="normal")
        self.history_box.delete("1.0", "end")
        self.history_box.configure(state="disabled")
        self._set_status("● Cleared — ready", "gray")

    def _on_close(self):
        self.stop_event.set()
        self.destroy()


# ── entry point ────────────────────────────────────────────

if __name__ == "__main__":
    app = InterviewAssistantApp()
    app.mainloop()
