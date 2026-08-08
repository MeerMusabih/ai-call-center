import logging
import asyncio
import json
import base64
from fastapi import WebSocket, WebSocketDisconnect

from app.config import settings
from app.utils.sessions import session_manager
from app.ai.rag import RAGPipeline
from app.faq.store import FAQStore
from app.voice.stt import SpeechToText
from app.voice.tts import TextToSpeech
from app.utils.audio import convert_mulaw_to_pcm, convert_pcm_to_mulaw
from app.utils.call_logger import CallLogger
from app.models.schemas import TranscriptEntry, Language
from datetime import datetime

logger = logging.getLogger(__name__)

faq_store = FAQStore()
rag = RAGPipeline(faq_store=faq_store)
stt = SpeechToText()
tts = TextToSpeech()
call_logger = CallLogger()


class VoiceWebSocketHandler:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def handle_connection(self, websocket: WebSocket, call_id: str):
        await websocket.accept()
        self.active_connections[call_id] = websocket
        logger.info(f"WebSocket connected for call {call_id}")

        session = session_manager.get_session(call_id)
        if not session:
            logger.warning(f"No session found for call {call_id}")
            await websocket.close(code=1008)
            return

        language = session.language.value if session.language else "en"
        audio_buffer = bytearray()
        stream_sid = None

        try:
            greeting = await rag.get_greeting(language)
            greeting_audio = await tts.synthesize(greeting, language)
            mulaw_audio = convert_pcm_to_mulaw(greeting_audio, settings.tts_sample_rate)
            await self._send_media(websocket, mulaw_audio, stream_sid)

            session.transcript.append(TranscriptEntry(
                role="assistant",
                text=greeting,
                language=Language(language),
            ))

            while True:
                raw = await websocket.receive_text()
                data = json.loads(raw)

                event = data.get("event")

                if event == "connected":
                    logger.info(f"Call {call_id}: Twilio media stream connected")

                elif event == "start":
                    stream_sid = data.get("streamSid")
                    logger.info(f"Call {call_id}: stream started, streamSid={stream_sid}")

                elif event == "media":
                    payload = data.get("media", {}).get("payload", "")
                    if payload:
                        chunk = base64.b64decode(payload)
                        audio_buffer.extend(chunk)

                        buffer_duration = len(audio_buffer) / settings.stt_sample_rate
                        if buffer_duration >= 2.0:
                            await self._process_utterance(
                                call_id, audio_buffer, session, websocket, language, stream_sid
                            )
                            audio_buffer = bytearray()

                elif event == "stop":
                    if audio_buffer and len(audio_buffer) > 100:
                        await self._process_utterance(
                            call_id, audio_buffer, session, websocket, language, stream_sid
                        )
                    logger.info(f"Call {call_id}: stream stopped")
                    break

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for call {call_id}")
        except Exception as e:
            logger.error(f"WebSocket error for call {call_id}: {e}", exc_info=True)
        finally:
            if call_id in self.active_connections:
                del self.active_connections[call_id]
            session.state = CallState.COMPLETED
            session.ended_at = datetime.now()
            call_logger.log_call(session)

    async def _send_media(self, websocket: WebSocket, mulaw_audio: bytes, stream_sid: str):
        if stream_sid:
            b64 = base64.b64encode(mulaw_audio).decode("ascii")
            chunk_size = 320
            for i in range(0, len(b64), chunk_size):
                await websocket.send_text(json.dumps({
                    "event": "media",
                    "streamSid": stream_sid,
                    "media": {"payload": b64[i:i + chunk_size]},
                }))
                await asyncio.sleep(0.02)
            await websocket.send_text(json.dumps({"event": "mark", "streamSid": stream_sid}))

    async def _process_utterance(
        self,
        call_id: str,
        audio_buffer: bytearray,
        session,
        websocket: WebSocket,
        language: str,
        stream_sid: str,
    ):
        if len(audio_buffer) < 800:
            return

        try:
            pcm_data = convert_mulaw_to_pcm(bytes(audio_buffer), settings.stt_sample_rate)
            transcript_text = await stt.transcribe_audio(
                bytes(pcm_data),
                language,
                sample_rate=settings.stt_sample_rate,
            )

            if not transcript_text.strip():
                return

            session.transcript.append(TranscriptEntry(
                role="user",
                text=transcript_text,
                language=Language(language),
            ))

            logger.info(f"Call {call_id} - User: {transcript_text}")

            response, _ = await rag.process_message(
                user_message=transcript_text,
                transcript=session.transcript,
                language=language,
            )

            session.transcript.append(TranscriptEntry(
                role="assistant",
                text=response,
                language=Language(language),
            ))

            logger.info(f"Call {call_id} - Assistant: {response}")

            response_audio = await tts.synthesize(response, language)
            mulaw_audio = convert_pcm_to_mulaw(response_audio, settings.tts_sample_rate)
            await self._send_media(websocket, mulaw_audio, stream_sid)

        except Exception as e:
            logger.error(f"Error processing utterance for call {call_id}: {e}", exc_info=True)


from app.models.schemas import CallState
voice_handler = VoiceWebSocketHandler()
