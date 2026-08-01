import logging
import asyncio
import edge_tts
import tempfile
import os

from app.config import settings

logger = logging.getLogger(__name__)

_FFMPEG_PATH = r"C:\Users\sirh9\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin"
if _FFMPEG_PATH not in os.environ.get("PATH", ""):
    os.environ["PATH"] = _FFMPEG_PATH + os.pathsep + os.environ.get("PATH", "")

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
            audio = audio.set_frame_rate(24000).set_channels(1).set_sample_width(2)

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
