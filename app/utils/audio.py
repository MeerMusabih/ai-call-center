import io
import logging
import os
import audioop
from pydub import AudioSegment

from app.config import settings
from app.utils.ffmpeg import ensure_ffmpeg_on_path

logger = logging.getLogger(__name__)

ensure_ffmpeg_on_path(settings.ffmpeg_path or None)


def convert_mulaw_to_pcm(mulaw_data: bytes, sample_rate: int = 8000) -> bytes:
    """Decode G.711 mu-law to 16-bit little-endian PCM."""
    pcm16 = audioop.ulaw2lin(mulaw_data, 2)
    audio = AudioSegment(
        data=pcm16,
        sample_width=2,
        frame_rate=sample_rate,
        channels=1,
    )
    return audio.raw_data


def convert_pcm_to_mulaw(pcm_data: bytes, sample_rate: int = 8000) -> bytes:
    """Encode 16-bit little-endian PCM (any rate) to G.711 mu-law at 8kHz."""
    audio = AudioSegment(
        data=pcm_data,
        sample_width=2,
        frame_rate=sample_rate,
        channels=1,
    )
    audio = audio.set_frame_rate(8000)
    return audioop.lin2ulaw(audio.raw_data, 2)


def convert_audio_format(
    audio_data: bytes,
    from_format: str,
    to_format: str,
    sample_rate: int = 8000,
) -> bytes:
    audio = AudioSegment(
        data=audio_data,
        sample_width=1 if from_format == "mulaw" else 2,
        frame_rate=sample_rate,
        channels=1,
    )

    if to_format == "mulaw":
        audio = audio.set_sample_width(1)
    elif to_format == "pcm":
        audio = audio.set_sample_width(2)

    return audio.raw_data


def get_audio_duration_ms(audio_data: bytes, sample_rate: int = 8000) -> int:
    audio = AudioSegment(
        data=audio_data,
        sample_width=1,
        frame_rate=sample_rate,
        channels=1,
    )
    return len(audio)
