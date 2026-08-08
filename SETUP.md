# AI Call Center - Install Guide

A voice customer-support demo. Callers press 1 for English or 2 for Arabic,
then speak questions to an AI agent that answers from a company FAQ. Works
with a browser (click-to-talk at `/voice/`) or a real phone (Twilio).

## Requirements

- Ubuntu/Debian Linux (or Windows 10/11 with WSL), 8+ GB RAM recommended
- Internet access for the first setup (models download automatically)

## Quick start (Linux)

```bash
chmod +x setup.sh
./setup.sh        # installs deps + downloads models (takes ~10-20 min)
./start.sh        # starts the server on port 8000
```

Then open:

- Voice console: `http://<this-host>:8000/voice/`
- FAQ management: `http://<this-host>:8000/voice/faq.html`
- Health check: `http://<this-host>:8000/health`

## What gets downloaded on first run

| Component | Model |
|-----------|-------|
| Speech-to-text | faster-whisper `medium` |
| Language model | Ollama `qwen2.5:1.5b` |
| Embeddings | `paraphrase-multilingual-MiniLM-L12-v2` |
| Text-to-speech | edge-tts (Azure neural voices, online) |

## Config

Copy `.env.example` to `.env` and edit if needed. Key settings:

- `WHISPER_MODEL` - STT accuracy vs speed (`base`/`small`/`medium`)
- `OLLAMA_MODEL` - the local LLM
- `FAQ_MAX_DISTANCE` - how close a question must be to an FAQ entry (0.33)
- `COMPANY_SIM_THRESHOLD` - company-vs-unrelated classifier cutoff (0.58)
- `TWILIO_*` - only needed for real phone calls

## FAQ knowledge base

Manage entries from the web UI at `/voice/faq.html` (add/remove/search).
Entries are saved to `data/faq/sample_faq.json`.

## Phone calls (Twilio, optional)

Set `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`,
and `TWILIO_WEBHOOK_URL` in `.env`, then expose port 8000 (or use a tunnel)
and point the webhook at `/webhook/call/incoming`.
