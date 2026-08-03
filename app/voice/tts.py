import logging
import asyncio
import edge_tts
import tempfile
import os
from typing import AsyncIterator

from app.config import settings
from app.utils.ffmpeg import ensure_ffmpeg_on_path

logger = logging.getLogger(__name__)

ensure_ffmpeg_on_path(settings.ffmpeg_path or None)

from pydub import AudioSegment

logger.info("Edge TTS initialized")


class TextToSpeech:
    def __init__(self):
        self.voices = {
            "en": settings.tts_voice_en,
            "ar": settings.tts_voice_ar,
        }

    async def synthesize(self, text: str, language: str) -> bytes:
        voice = self.voices.get(language, self.voices["en"])

        communicate = edge_tts.Communicate(text, voice)

        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                temp_path = f.name

            await communicate.save(temp_path)

            audio = AudioSegment.from_mp3(temp_path)
            audio = audio.set_frame_rate(settings.tts_sample_rate).set_channels(1).set_sample_width(2)

            return audio.raw_data

        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except PermissionError:
                    pass

    async def synthesize_to_file(self, text: str, language: str, output_path: str) -> str:
        voice = self.voices.get(language, self.voices["en"])

        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        return output_path

    async def stream_audio(self, text: str, language: str) -> AsyncIterator[bytes]:
        """Stream MP3 audio chunks as they are synthesized."""
        voice = self.voices.get(language, self.voices["en"])

        communicate = edge_tts.Communicate(text, voice)
        async for chunk in communicate.stream():
            if chunk.get("type") == "audio" and chunk.get("data"):
                yield chunk["data"]
