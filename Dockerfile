# ─────────────────────────────────────────────
# PrepPilot — Dockerfile
# Runs the terminal voice assistant (assistant.py)
# GUI requires a display; use docker-compose for full setup
# ─────────────────────────────────────────────

FROM python:3.12-slim

# System deps for pyaudio + portaudio
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    gcc \
    libasound2-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Default: run text assistant (no display needed in container)
CMD ["python", "text_assistant.py", "--model", "llama3.2"]
