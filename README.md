# AI Call Center

A production-oriented voice call center demo with **interactive voice response (IVR)**, **FAQ auto-answering**, and a **real-time voice chat** client. Callers can navigate a menu, ask questions in English or Arabic, and get natural-sounding answers from a local knowledge base.

Runs fully **on-premise / local** — no cloud AI APIs required. Every component (speech-to-text, language model, text-to-speech, knowledge search) runs locally, so there are no per-minute API fees and no call data leaves the machine.

---

## Features

- **IVR menu** with language selection (English / Arabic) and auto-answer on FAQ topics
- **FAQ retrieval-augmented answering** from a local vector store (ChromaDB)
- **Real-time voice chat** client (`voice_chat.bat`) for live spoken Q&A through the microphone
- **Local speech pipeline**: faster-whisper (STT) + edge-tts (TTS) + Ollama LLM
- **Twilio Media Streams integration** for real phone calls (configurable webhook)
- **Web dashboard** served at `/dashboard/` with live call stats
- **Call logging** to `data/calls/` with structured records
- **Docker + Cloud Run** deployment templates included

---

## Architecture

```
                    ┌────────────────────────────────────────┐
                    │            FastAPI server               │
                    │                                        │
  Twilio / Voice ──►│  IVR menu → FAQ search → LLM → TTS     │
  Chat client       │                                        │
                    └───────────────┬────────────────────────┘
                                    │
                 ┌──────────────────┼──────────────────┐
                 ▼                  ▼                  ▼
          ChromaDB (FAQ)      Ollama (LLM)      edge-tts (voice)
          + embeddings        qwen2.5:1.5b
```

| Layer | Technology | Model |
|-------|-----------|-------|
| Speech-to-text | faster-whisper | `base` (local) |
| Language model | Ollama | `qwen2.5:1.5b` (local) |
| Text-to-speech | edge-tts | Azure neural voices (EN/AR) |
| Knowledge base | ChromaDB + sentence-transformers | `all-MiniLM-L6-v2` |
| API / streaming | FastAPI + WebSockets | — |

---

## Requirements

- **Windows 10/11** (mic support) or **Ubuntu/Debian Linux** (server / VM)
- **Python 3.10–3.12**
- **Ollama** — https://ollama.com/download
- **FFmpeg** — required by audio processing (must be on `PATH`; the app auto-detects it)
- **~8 GB RAM** recommended
- Microphone and speakers for the voice chat demo

---

## Setup

### Linux (Ubuntu/Debian)

```bash
./setup.sh     # installs deps, Ollama, model pull, venv, .env
./start.sh     # starts Ollama + FastAPI server on port 8000
```

### Windows

### 1. Install Ollama and pull the LLM

```bat
:: install Ollama from https://ollama.com/download, then:
ollama serve
ollama pull qwen2.5:1.5b
```

### 2. Create a virtual environment

```bat
cd ai-call-center
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment

```bat
copy .env.example .env
```

Edit `.env` and set:

| Variable | Description |
|----------|-------------|
| `OLLAMA_MODEL` | Ollama model name (e.g. `qwen2.5:1.5b`) |
| `TWILIO_*` | Optional — only needed for real phone calls |
| `TTS_VOICE_EN` / `TTS_VOICE_AR` | Voice names for English / Arabic |

### 4. Add your FAQ content

Edit `data/faq/sample_faq.json` — add Q&A entries in English and Arabic. The vector store is rebuilt automatically on startup.

---

## Running

### Local voice chat demo (no Twilio needed)

```
voice_chat.bat
```

This starts Ollama + the FastAPI server (if not already running) and launches the interactive mic client: press **ENTER**, speak, and the assistant replies aloud.

### Server only

```
start.bat
```

Then open:

- Dashboard: http://localhost:8000/dashboard/
- Health: http://localhost:8000/health
- API docs: http://localhost:8000/docs

### Twilio phone integration

1. `ngrok http 8000`
2. Set `TWILIO_WEBHOOK_URL` in `.env` to `https://<your-ngrok-domain>/webhook/call/incoming`
3. Point your Twilio number's voice webhook at the same URL and fill in `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`

---

## Project structure

```
ai-call-center/
├── app/
│   ├── ai/            # LLM client + retrieval-augmented answering
│   ├── faq/           # FAQ ingestion, embeddings, vector store
│   ├── ivr/           # IVR menu and greetings
│   ├── models/        # Pydantic schemas
│   ├── telephony/     # Twilio adapter (Media Streams)
│   ├── utils/         # sessions, call logging, audio helpers
│   ├── voice/         # STT, TTS, WebSocket streaming
│   ├── config.py      # settings (loaded from .env)
│   └── main.py        # FastAPI app + endpoints
├── data/
│   ├── faq/           # FAQ source content (JSON)
│   ├── calls/         # call logs (generated)
│   └── chroma/        # vector store (generated)
├── dashboard/         # web dashboard
├── deploy/            # Cloud Run template
├── docker/            # Dockerfile
├── tests/             # tests
├── voice_chat.py      # local voice chat client
├── start.bat          # server launcher
├── voice_chat.bat     # voice chat launcher
└── requirements.txt
```

---

## Deployment

- **Docker**: `docker build -t ai-call-center . && docker run -p 8000:8000 ai-call-center`
- **Cloud Run**: see `deploy/cloud_run.yaml` (set `PROJECT_ID` and `GOOGLE_CLOUD_PROJECT`)

---

## License

Proprietary — for demonstration and evaluation purposes.
