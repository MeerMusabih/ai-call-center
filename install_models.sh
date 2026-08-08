#!/usr/bin/env bash
# AI Call Center - install bundled offline models (Option B bundle)
# Copies the models that ship in this package into their runtime locations.
set -euo pipefail

cd "$(dirname "$0")"

SUDO=""
if [ "$(id -u)" -ne 0 ]; then
  if command -v sudo >/dev/null 2>&1; then SUDO="sudo"; else
    echo "[!] Must run as root or have sudo." >&2; exit 1
  fi
fi

echo "[1/3] Installing HuggingFace model cache..."
mkdir -p "$HOME/.cache/huggingface"
cp -rn models-hf-cache/. "$HOME/.cache/huggingface/"
echo "[OK] HF cache installed at $HOME/.cache/huggingface"

echo "[2/3] Installing Ollama model (qwen2.5:1.5b)..."
if ! command -v ollama >/dev/null 2>&1; then
  echo "[!] Ollama is not installed. Run ./setup.sh first, then re-run this script." >&2
  exit 1
fi
# Stop ollama so we can write its model store
if pgrep -f "ollama serve" >/dev/null 2>&1; then
  $SUDO systemctl stop ollama 2>/dev/null || $SUDO pkill -f "ollama serve" 2>/dev/null || true
fi

OLLAMA_HOME="${OLLAMA_HOME:-}"
if [ -z "$OLLAMA_HOME" ]; then
  OLLAMA_USER_HOME="$HOME/.ollama"
  SYS_HOME="/usr/share/ollama"
  if [ -d "$SYS_HOME/.ollama" ]; then OLLAMA_HOME="$SYS_HOME/.ollama"; else OLLAMA_HOME="$OLLAMA_USER_HOME"; fi
fi
echo "  Ollama home: $OLLAMA_HOME"
mkdir -p "$OLLAMA_HOME/models"
cp -rn ollama-models/. "$OLLAMA_HOME/models/"

if [ "$OLLAMA_HOME" = "$SYS_HOME/.ollama" ]; then
  $SUDO chown -R ollama:ollama "$OLLAMA_HOME" 2>/dev/null || true
fi

# Restart ollama
$SUDO systemctl start ollama 2>/dev/null || nohup ollama serve >/tmp/ollama.log 2>&1 &
sleep 4

echo "[3/3] Verifying..."
if curl -s http://localhost:11434/api/tags | grep -q "qwen2.5:1.5b"; then
  echo "[OK] qwen2.5:1.5b is available offline."
else
  echo "[!] Model not detected. Run: ollama list"
fi
echo "Done. Start the server with ./start.sh"
