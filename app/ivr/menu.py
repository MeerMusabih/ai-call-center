import logging
from fastapi import APIRouter, Form
from fastapi.responses import PlainTextResponse

from app.ivr.greetings import (
    build_ivr_response,
    build_timeout_response,
)
from app.models.schemas import Language
from app.utils.sessions import session_manager
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ivr", tags=["ivr"])


def twiml_response(twiml: str) -> PlainTextResponse:
    return PlainTextResponse(content=twiml, media_type="application/xml")


def _build_stream_twiml(language: str, call_id: str) -> str:
    from twilio.twiml.voice_response import VoiceResponse

    ws_url = settings.twilio_webhook_url.replace("https://", "wss://").replace("http://", "ws://")
    ws_url = ws_url.rstrip("/") + f"/ws/voice/{call_id}"

    lang_attr = "ar-XA" if language == "ar" else "en-US"
    greeting = "مرحباً بك! كيف يمكنني مساعدتك اليوم؟" if language == "ar" else "Hello! How can I help you today?"

    response = VoiceResponse()
    response.say(greeting, language=lang_attr)
    response.pause(length=1)

    connect = response.connect()
    connect.stream(url=ws_url)

    return str(response)


@router.post("/answer")
async def ivr_answer():
    twiml = build_ivr_response()
    return twiml_response(twiml)


@router.post("/selected")
async def ivr_selected(
    CallSid: str = Form(...),
    Digit: str = Form(None),
    Digits: str = Form(None),
):
    digit = Digits if Digit is None else Digit
    language = None
    if digit == "1":
        language = Language.ENGLISH
    elif digit == "2":
        language = Language.ARABIC
    else:
        twiml = build_timeout_response(0)
        return twiml_response(twiml)

    session = session_manager.get_session(CallSid)
    if session:
        session.language = language
        session.state = "active"
    else:
        session = session_manager.create_session(
            call_id=CallSid, phone_number="unknown"
        )
        session.language = language
        session.state = "active"

    twiml = _build_stream_twiml(language.value, CallSid)
    logger.info(f"Call {CallSid}: language selected = {language.value}, streaming started")
    return twiml_response(twiml)


@router.post("/timeout")
async def ivr_timeout(
    CallSid: str = Form(...),
    retry: int = Form(0),
):
    session = session_manager.get_session(CallSid)
    lang = session.language.value if session and session.language else "en"
    twiml = build_timeout_response(retry, lang)
    return twiml_response(twiml)
