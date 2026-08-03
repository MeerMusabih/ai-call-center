import asyncio
import logging
from typing import AsyncIterator
from twilio.rest import Client as TwilioClient
from twilio.twiml.voice_response import VoiceResponse, Gather

from app.config import settings
from app.telephony.base import TelephonyAdapter

logger = logging.getLogger(__name__)


class TwilioAdapter(TelephonyAdapter):
    def __init__(self):
        self.client = None
        self.from_number = settings.twilio_phone_number
        if settings.twilio_account_sid and settings.twilio_auth_token:
            self.client = TwilioClient(
                settings.twilio_account_sid, settings.twilio_auth_token
            )
            logger.info("Twilio adapter initialized")
        else:
            logger.warning("Twilio credentials not configured, adapter in stub mode")

    async def answer_call(self, call_id: str) -> dict:
        response = VoiceResponse()
        response.say("Welcome.", language="en-US")
        gather = Gather(
            num_digits=1,
            timeout=settings.ivr_timeout_seconds,
            action=f"{settings.twilio_webhook_url}/webhook/ivr/selected",
            method="POST",
        )
        gather.say(
            "Press 1 for English. Press 2 for Arabic.",
            language="en-US",
        )
        response.append(gather)
        response.redirect(f"{settings.twilio_webhook_url}/webhook/ivr/timeout", method="POST")
        return {"twiml": str(response)}

    async def hangup_call(self, call_id: str) -> dict:
        response = VoiceResponse()
        response.hangup()
        return {"twiml": str(response)}

    async def play_audio(self, call_id: str, audio_url: str) -> dict:
        response = VoiceResponse()
        response.play(audio_url)
        return {"twiml": str(response)}

    async def gather_dtmf(self, call_id: str, num_digits: int, timeout: int) -> dict:
        response = VoiceResponse()
        gather = Gather(
            num_digits=num_digits,
            timeout=timeout,
            action=f"{settings.twilio_webhook_url}/webhook/ivr/selected",
            method="POST",
        )
        response.append(gather)
        return {"twiml": str(response)}

    async def stream_audio(self, call_id: str, audio_chunks: AsyncIterator[bytes]) -> None:
        pass

    def get_webhook_routes(self) -> list:
        return []

    async def start_recording(self, call_id: str) -> str:
        if not self.client:
            logger.warning("Twilio not configured, skipping recording")
            return call_id
        call = await asyncio.to_thread(
            self.client.calls(call_id).update,
            record=True,
            recording_status_callback=f"{settings.twilio_webhook_url}/recording/status",
        )
        return call.sid

    async def stop_recording(self, call_id: str) -> str:
        if not self.client:
            return call_id
        recordings = await asyncio.to_thread(
            self.client.recordings.list, call_sid=call_id
        )
        for recording in recordings:
            await asyncio.to_thread(
                self.client.recordings(recording.sid).delete
            )
        return call_id

    async def send_twiml(self, call_id: str, twiml: str) -> dict:
        if not self.client:
            return {"call_sid": call_id}
        call = await asyncio.to_thread(
            self.client.calls(call_id).update, twiml=twiml
        )
        return {"call_sid": call.sid}
