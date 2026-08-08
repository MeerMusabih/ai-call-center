# AI Call Center

A self-contained, **fully local** voice call-center demo. Callers dial in (or open the browser), choose **English or Arabic**, and ask questions that the agent answers from a company FAQ — with natural voice replies, real-time speech recognition, and a management UI for the knowledge base.

Everything runs **on-premise / offline-ready**: speech-to-text (faster-whisper), language model (Ollama), embeddings, and knowledge search are all local. Text-to-speech uses Microsoft's free edge-tts neural voices. No cloud AI APIs, no per-minute fees, no call data leaving the machine.

---

## Features

- **IVR start flow** — press 1 for English or 2 for Arabic, hear a greeting, then talk
- **FAQ auto-answering** — retrieval-augmented answers from a local ChromaDB vector store, in English and Arabic
- **Conversational fallbacks** — company-topic questions not in the FAQ get a "let me connect you to a human agent" decline; unrelated small-talk gets a polite "I can only help with Acme" decline
- **Meta-question coverage** — "Who am I talking to?", "What can you do?", "What services do you provide?" are answered from the FAQ
- **Real-time voice chat** — browser click-to-talk at `/voice/` (no Twilio needed) with a live audio meter
- **FAQ management UI** — add, remove, search, and language-filter entries live at `/voice/faq.html` (no restart needed)
- **Local speech pipeline** — faster-whisper `medium` (STT) + edge-tts (TTS) + Ollama `qwen2.5:1.5b` (LLM)
- **Twilio Media Streams integration** for real phone calls (optional)
- **Web dashboard** at `/dashboard/` with live call stats
- **Call logging** to `data/calls/` with structured records
- **Docker + Cloud Run** deployment templates included

---

## How it decides what to answer

When a caller speaks, the server:

1. **Transcribes** audio with faster-whisper (medium, VAD-filtered)
2. **Searches the FAQ** by multilingual embedding similarity
   - close match (`≤ FAQ_MAX_DISTANCE` = 0.33) → answer from FAQ
3. **Classifies the topic** as company-related or not
   - company-related, no FAQ match → **human-agent decline**
   - unrelated → **company-only decline**
4. **Speaks** the reply with edge-tts in the caller's chosen language

`/api/test-call` reports the source of every response (`faq` | `company` | `unrelated`) so you can audit behavior without picking up the phone.

---

## Architecture

```
                    ┌────────────────────────────────────┐
                    │           FastAPI server            │
                    │                                     │
  Twilio / Voice ──►│  IVR → STT → FAQ search → LLM → TTS │
  Chat client       │                                     │
                    └───────────────┬─────────────────────┘
                                    │
                 ┌──────────────────┼──────────────────┐
                 ▼                  ▼                  ▼
          ChromaDB (FAQ)      Ollama (LLM)      edge-tts (voice)
          + embeddings        qwen2.5:1.5b
```

| Layer | Technology | Model |
|-------|-----------|-------|
| Speech-to-text | faster-whisper | `medium`, int8, beam 5, VAD |
| Language model | Ollama | `qwen2.5:1.5b` (local) |
| Text-to-speech | edge-tts | Azure neural voices (EN/AR) |
| Knowledge base | ChromaDB + sentence-transformers | `paraphrase-multilingual-MiniLM-L12-v2` |
| API / streaming | FastAPI + WebSockets | — |

---

## Requirements

- **Ubuntu/Debian Linux** (server / VM) or **Windows 10/11** with WSL
- **Python 3.10–3.12**
- **Ollama** — https://ollama.com/download
- **FFmpeg** — required for audio processing (must be on `PATH`)
- **~8 GB RAM** recommended (the medium Whisper model is the heaviest part)
- Microphone + speakers for the browser voice demo

---

## Installation

### Option A — source only (needs internet on first run)

```bash
git clone https://github.com/MeerMusabih/ai-call-center.git
cd ai-call-center
./setup.sh     # system deps, Ollama, venv, pip deps, model downloads (~10–20 min)
./start.sh     # starts Ollama + FastAPI server on port 8000
```

### Option B — full offline bundle

Download all chunks from the [latest release](https://github.com/MeerMusabih/ai-call-center/releases):

```bash
tar -xzf ai-call-center-full.tar.gz     # after reassembling via REASSEMBLE.sh
cd ai-call-center
./setup.sh            # system deps + venv + pip (internet needed once)
./install_models.sh   # copies bundled whisper/embedding/LLM models into place
./start.sh
```

### Windows

```bat
ollama serve
ollama pull qwen2.5:1.5b
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
start.bat
```

---

## Running

Open:

- **Voice console (click-to-talk):** http://localhost:8000/voice/ — click **Start Conversation**, press 1/2 for language, then hold-to-talk
- **FAQ management:** http://localhost:8000/voice/faq.html
- **Dashboard:** http://localhost:8000/dashboard/
- **Health:** http://localhost:8000/health
- **API docs:** http://localhost:8000/docs

### Twilio phone integration (optional)

1. `ngrok http 8000`
2. Set `TWILIO_WEBHOOK_URL` in `.env` to `https://<your-ngrok-domain>/webhook/call/incoming`
3. Point your Twilio number's voice webhook at the same URL; fill in `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`

---

## Configuration (`.env`)

Copy `.env.example` to `.env` and edit. Key settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_MODEL` | `qwen2.5:1.5b` | Local LLM |
| `WHISPER_MODEL` | `medium` | STT model (`base`/`small`/`medium`) |
| `WHISPER_CPU_THREADS` | `4` | Threads for STT |
| `EMBEDDING_MODEL` | `paraphrase-multilingual-MiniLM-L12-v2` | FAQ embeddings |
| `FAQ_MAX_DISTANCE` | `0.33` | Max embedding distance for an FAQ match |
| `COMPANY_SIM_THRESHOLD` | `0.58` | Company-vs-unrelated classifier cutoff |
| `WEB_SEARCH_ENABLED` | `false` | Optional free web-search fallback |
| `LLM_PROVIDER` | `local` | `local` (Ollama) or `azure_openai` |
| `TTS_VOICE_EN` / `TTS_VOICE_AR` | Ava / Zariyah | English / Arabic voices |
| `TWILIO_*` | — | Only needed for real phone calls |

The FAQ lives in `data/faq/sample_faq.json` (62 entries, EN + AR). Manage it from the web UI — changes apply immediately, no restart.

---

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/faq` | List FAQ entries |
| `POST` | `/api/faq` | Add FAQ entry |
| `DELETE` | `/api/faq/{item_id}` | Remove FAQ entry |
| `POST` | `/api/faq/ingest` | Rebuild vector store from JSON |
| `POST` | `/api/faq/refresh` | Re-sync vectors |
| `POST` | `/api/test-call` | Simulate a call; returns `source` (faq/company/unrelated) |
| `POST` | `/api/stt` | Transcribe audio |
| `POST` | `/api/tts` | Synthesize speech |
| `GET` | `/api/tts/stream` | Stream TTS audio |
| `GET` | `/api/calls` / `/api/sessions` | Call logs and sessions |
| `WS` | `/ws/stt` | Live speech-to-text |
| `WS` | `/ws/voice/{call_id}` | Full duplex voice session |

---

## Project structure

```
ai-call-center/
├── app/
│   ├── ai/            # LLM client + RAG answering + topic classifier
│   ├── faq/           # FAQ ingestion, embeddings, vector store, CRUD
│   ├── ivr/           # IVR menu and greetings
│   ├── models/        # Pydantic schemas
│   ├── telephony/     # Twilio adapter (Media Streams)
│   ├── utils/         # sessions, call logging, audio helpers
│   ├── voice/         # STT, TTS, WebSocket streaming
│   ├── config.py      # settings (loaded from .env)
│   └── main.py        # FastAPI app + endpoints
├── data/
│   ├── faq/           # FAQ source content (JSON) — edit here or via web UI
│   ├── calls/         # call logs (generated)
│   └── chroma/        # vector store (generated)
├── voice_client/      # browser console (voice + FAQ management)
├── dashboard/         # web dashboard
├── deploy/            # Cloud Run template
├── docker/            # Dockerfile
├── voice_chat.py      # local voice chat client
├── setup.sh           # one-click Linux installer
├── install_models.sh  # installs bundled offline models (full bundle)
├── start.sh           # server launcher
└── requirements.txt
```

---

## Deployment

- **Docker:** `docker build -t ai-call-center . && docker run -p 8000:8000 ai-call-center`
- **Cloud Run:** see `deploy/cloud_run.yaml` (set `PROJECT_ID` and `GOOGLE_CLOUD_PROJECT`)

See [SETUP.md](SETUP.md) for the full recipient install guide.

---

## License

Proprietary — for demonstration and evaluation purposes.
