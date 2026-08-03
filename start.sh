#!/usr/bin/env bash
# AI Call Center - Linux server launcher
# Starts Ollama (if not running), pulls the model, then runs the FastAPI server.
set -euo pipefail

cd "$(dirname "$0")"

export PATH="$HOME/.local/bin:$PATH"

OLLAMA_MODEL="${OLLAMA_MODEL:-qwen2.5:1.5b}"

echo "[1/3] Checking Ollama..."
if ! curl -s http://localhost:11434/api/version >/dev/null 2>&1; then
  if command -v ollama >/dev/null 2>&1; then
    echo "  Starting Ollama..."
    nohup ollama serve >/tmp/ollama.log 2>&1 &
    sleep 4
  else
    echo "[!] Ollama not found. Run ./setup.sh first." >&2
    exit 1
  fi
fi
echo "[OK] Ollama running"

echo "[2/3] Ensuring model ${OLLAMA_MODEL} is available..."
ollama pull "${OLLAMA_MODEL}" >/dev/null 2>&1 || echo "  (model pull failed - check Ollama)"

echo "[3/3] Starting FastAPI server on port 8000..."
if [ ! -x ".venv/bin/python" ]; then
  echo "[!] Virtual env missing. Run ./setup.sh first." >&2
  exit 1
fi
exec .venv/bin/python run_server.py
