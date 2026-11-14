#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "=== AI Video Clipper setup ==="
if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required. Install it from https://brew.sh and run this script again."
  exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "Installing FFmpeg..."
  brew install ffmpeg
fi

if ! command -v ollama >/dev/null 2>&1; then
  echo "Installing Ollama..."
  brew install ollama
fi

if ! command -v python3.11 >/dev/null 2>&1; then
  echo "Installing Python 3.11..."
  brew install python@3.11
fi

if [ ! -d ".venv" ]; then
  python3.11 -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if ! curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  echo "Starting local Ollama service..."
  nohup ollama serve >/tmp/ai-video-clipper-ollama.log 2>&1 &
  for attempt in $(seq 1 30); do
    if curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
      break
    fi
    sleep 2
  done
fi

if ! curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  echo "Ollama did not start. Check /tmp/ai-video-clipper-ollama.log"
  exit 1
fi

echo "Downloading the local AI model (first run only)..."
ollama pull llama3.1

echo
echo "Starting AI Video Clipper. Keep this Terminal window open."
echo "A temporary public Gradio URL will appear below."
echo "Anyone with that URL can access the app unless you configure APP_USERNAME and APP_PASSWORD."
echo
python app.py
