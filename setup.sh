#!/usr/bin/env bash
# AI Call Center - one-click setup for Ubuntu/Debian (and most Linux distros)
set -euo pipefail

cd "$(dirname "$0")"

OLLAMA_MODEL="${OLLAMA_MODEL:-qwen2.5:1.5b}"
WHISPER_MODEL="${WHISPER_MODEL:-medium}"
EMBEDDING_MODEL="${EMBEDDING_MODEL:-sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2}"

echo "=============================================="
echo "  AI Call Center - Linux setup"
echo "=============================================="

SUDO=""
if [ "$(id -u)" -ne 0 ]; then
  if command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
  else
    echo "[!] Must run as root or have sudo." >&2
    exit 1
  fi
fi

echo "[1/6] Installing system packages (ffmpeg, python3, venv, portaudio)..."
$SUDO apt-get update -y
$SUDO apt-get install -y \
    curl \
    git \
    python3 \
    python3-venv \
    python3-pip \
    ffmpeg \
    libportaudio2 \
    build-essential \
    pkg-config

echo "[2/6] Installing Ollama..."
if ! command -v ollama >/dev/null 2>&1 && [ ! -x "$HOME/.local/bin/ollama" ]; then
  curl -fsSL https://ollama.com/install.sh | sh
fi
export PATH="$HOME/.local/bin:$PATH"
if command -v ollama >/dev/null 2>&1; then
  echo "[OK] Ollama installed: $(ollama --version)"
else
  echo "[!] Ollama install failed. Install manually from https://ollama.com/download/linux"
fi

echo "[3/6] Creating Python virtual environment..."
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
. .venv/bin/activate
python -m pip install --upgrade pip

echo "[4/6] Installing Python dependencies (this downloads torch/whisper, may take a while)..."
pip install -r requirements.txt

echo "[5/6] Creating .env from example..."
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "[OK] Created .env (edit it with your real credentials if needed)"
else
  echo "[OK] .env already exists"
fi

echo "[6/6] Pre-downloading models (embedding + whisper)..."
python - <<PYEOF
from sentence_transformers import SentenceTransformer
SentenceTransformer("${EMBEDDING_MODEL}")
print("embedding model ready")
PYEOF
python - <<PYEOF
from faster_whisper import WhisperModel
WhisperModel("${WHISPER_MODEL}", device="cpu", compute_type="int8")
print("whisper model ready")
PYEOF

echo "[+] Pulling Ollama model ${OLLAMA_MODEL} (may take a few minutes)..."
if command -v ollama >/dev/null 2>&1; then
  nohup ollama serve >/tmp/ollama.log 2>&1 &
  sleep 4
  ollama pull "${OLLAMA_MODEL}"
fi

echo ""
echo "=============================================="
echo "  Setup complete!"
echo ""
echo "  Start the server:   ./start.sh"
echo "  Dashboard:          http://<this-host>:8000/dashboard/"
echo "  Health check:       http://<this-host>:8000/health"
echo "=============================================="
