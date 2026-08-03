import asyncio
import logging
import os
import numpy as np
from faster_whisper import WhisperModel

from app.config import settings
from app.utils.ffmpeg import ensure_ffmpeg_on_path

logger = logging.getLogger(__name__)

ensure_ffmpeg_on_path(settings.ffmpeg_path or None)

STT_MAX_CONCURRENCY = 4
_stt_semaphore = asyncio.Semaphore(STT_MAX_CONCURRENCY)


class SpeechToText:
    def __init__(self):
        self.model = WhisperModel(
            settings.whisper_model,
            device="cpu",
            compute_type="int8",
        )
        logger.info(f"Whisper model loaded: {settings.whisper_model}")

    async def transcribe_audio(self, audio_data: bytes, language: str, sample_rate: int = 16000) -> str:
        async with _stt_semaphore:
            return await asyncio.to_thread(
                self._transcribe_blocking, audio_data, language, sample_rate
            )

    def _transcribe_blocking(self, audio_data: bytes, language: str, sample_rate: int = 16000) -> str:
        from pydub import AudioSegment

        audio = AudioSegment(
            data=audio_data,
            sample_width=2,
            frame_rate=sample_rate,
            channels=1,
        )

        audio = audio.set_frame_rate(16000).set_channels(1)
        audio_np = np.array(audio.get_array_of_samples(), dtype=np.float32) / 32768.0

        whisper_lang = "ar" if language == "ar" else "en"

        segments, _ = self.model.transcribe(
            audio_np,
            language=whisper_lang,
            beam_size=1,
        )

        text = " ".join(segment.text for segment in segments)
        return text.strip()

    async def transcribe_stream(self, audio_chunks: list[bytes], language: str) -> list[str]:
        combined = b"".join(audio_chunks)
        text = await self.transcribe_audio(combined, language)
        return [text] if text else []
