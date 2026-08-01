import logging
import uuid
from datetime import datetime

from fastapi import FastAPI, WebSocket, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from twilio.twiml.voice_response import VoiceResponse

from app.config import settings
from app.utils.ffmpeg import ensure_ffmpeg_on_path

ensure_ffmpeg_on_path(settings.ffmpeg_path or None)

from app.ivr.menu import router as ivr_router
from app.voice.stream import voice_handler, rag, tts, faq_store, stt
from app.utils.sessions import session_manager
from app.utils.call_logger import CallLogger
from app.models.schemas import HealthResponse, CallState, Language

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Call Center",
    description="AI-powered voice call center with FAQ support",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ivr_router, prefix="/webhook")

call_logger = CallLogger()


@app.on_event("startup")
async def startup():
    logging.basicConfig(level=settings.log_level)
    logger.info("Starting AI Call Center")
    faq_store.initialize()


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        environment=settings.environment,
    )


@app.post("/webhook/call/incoming")
async def incoming_call(
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
):
    session = session_manager.create_session(
        call_id=CallSid,
        phone_number=From,
    )

    response = VoiceResponse()
    gather = response.gather(
        num_digits=1,
        timeout=settings.ivr_timeout_seconds,
        action=f"{settings.twilio_webhook_url}/webhook/ivr/selected",
        method="POST",
    )
    gather.say("Welcome. Press 1 for English. Press 2 for Arabic.", language="en-US")
    response.redirect(f"{settings.twilio_webhook_url}/webhook/ivr/timeout", method="POST")

    return PlainTextResponse(content=str(response), media_type="application/xml")


@app.post("/webhook/call/status")
async def call_status(
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
):
    session = session_manager.get_session(CallSid)
    if session:
        if CallStatus in ("completed", "busy", "no-answer", "canceled"):
            session.state = CallState.COMPLETED
            session.ended_at = datetime.now()
            call_logger.log_call(session)

    return {"status": "ok"}


@app.websocket("/ws/voice/{call_id}")
async def voice_websocket(websocket: WebSocket, call_id: str):
    await voice_handler.handle_connection(websocket, call_id)


@app.post("/api/test-call")
async def test_call(body: dict = Body(...)):
    message = body.get("message", "")
    language = body.get("language", "en")
    call_id = body.get("call_id", str(uuid.uuid4()))

    if not message:
        return {"error": "message is required"}

    session = session_manager.get_session(call_id)
    if not session:
        session = session_manager.create_session(call_id=call_id, phone_number="test")
    session.language = Language(language)
    session.state = "active"

    from app.models.schemas import TranscriptEntry

    import time as _t
    t0 = _t.time()

    response_text = await rag.process_message(
        user_message=message,
        transcript=session.transcript,
        language=language,
    )

    t1 = _t.time()
    logger.info(f"[TIMING] test-call total={t1-t0:.2f}s")

    session.transcript.append(TranscriptEntry(
        role="user", text=message, language=Language(language),
    ))
    session.transcript.append(TranscriptEntry(
        role="assistant", text=response_text, language=Language(language),
    ))

    return {
        "call_id": call_id,
        "response": response_text,
        "transcript_length": len(session.transcript),
    }


@app.post("/api/stt")
async def transcribe_speech(body: dict = Body(...)):
    import base64

    audio_b64 = body.get("audio", "")
    language = body.get("language", "en")
    sample_rate = body.get("sample_rate", 16000)

    if not audio_b64:
        return {"error": "audio (base64) is required"}

    import binascii
    try:
        audio_data = base64.b64decode(audio_b64)
    except binascii.Error:
        return {"error": "invalid base64 audio"}

    text = await stt.transcribe_audio(audio_data, language, sample_rate=sample_rate)
    return {"text": text}


@app.post("/api/tts")
async def synthesize_speech(body: dict = Body(...)):
    import base64

    text = body.get("text", "")
    language = body.get("language", "en")

    if not text:
        return {"error": "text is required"}

    audio_data = await tts.synthesize(text, language)
    return {
        "audio": base64.b64encode(audio_data).decode("ascii"),
        "sample_rate": 24000,
        "sample_width": 2,
        "channels": 1,
    }


@app.get("/api/calls")
async def get_calls():
    return call_logger.get_all_call_logs()


@app.get("/api/calls/{call_id}")
async def get_call(call_id: str):
    log = call_logger.get_call_log(call_id)
    if not log:
        return {"error": "Call not found"}
    return log


@app.get("/api/sessions")
async def get_sessions():
    sessions = session_manager.get_all_sessions()
    return [s.model_dump() for s in sessions]


@app.get("/api/sessions/{call_id}")
async def get_session(call_id: str):
    session = session_manager.get_session(call_id)
    if not session:
        return {"error": "Session not found"}
    return session.model_dump()


@app.get("/api/faq")
async def get_faq():
    return faq_store.get_all()


@app.post("/api/faq/ingest")
async def ingest_faq(file_path: str):
    from app.faq.ingestion import FAQIngestion
    ingestion = FAQIngestion()
    items = ingestion.load_file(file_path)
    faq_store.ingest_items(items)
    return {"message": f"Ingested {len(items)} FAQ items"}


@app.post("/api/faq/refresh")
async def refresh_faq():
    faq_store._initialized = False
    faq_store.initialize()
    return {"message": "FAQ store refreshed"}


dashboard_dir = os.path.join(os.path.dirname(__file__), "..", "dashboard")
if os.path.isdir(dashboard_dir):
    app.mount("/dashboard", StaticFiles(directory=dashboard_dir, html=True), name="dashboard")
