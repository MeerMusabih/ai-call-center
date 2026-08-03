import logging
import os
import shutil

logger = logging.getLogger(__name__)

_COMMON_FFMPEG_BIN_DIRS = [
    r"C:\Program Files\ffmpeg\bin",
    r"C:\ffmpeg\bin",
    r"C:\ProgramData\chocolatey\bin",
    "/usr/bin",
    "/usr/local/bin",
    "/opt/ffmpeg/bin",
]

_FFMPEG_BIN_NAMES = ["ffmpeg.exe", "ffmpeg"]


def _find_ffmpeg_dir() -> str | None:
    if shutil.which("ffmpeg"):
        return None

    for d in _COMMON_FFMPEG_BIN_DIRS:
        for name in _FFMPEG_BIN_NAMES:
            if os.path.isfile(os.path.join(d, name)):
                return d

    return None


def ensure_ffmpeg_on_path(custom_dir: str | None = None) -> None:
    """Add an FFmpeg bin directory to PATH if ffmpeg is not already available."""
    if shutil.which("ffmpeg"):
        return

    if custom_dir and any(
        os.path.isfile(os.path.join(custom_dir, name)) for name in _FFMPEG_BIN_NAMES
    ):
        os.environ["PATH"] = custom_dir + os.pathsep + os.environ.get("PATH", "")
        logger.info("Using FFmpeg from %s", custom_dir)
        return

    found = _find_ffmpeg_dir()
    if found:
        os.environ["PATH"] = found + os.pathsep + os.environ.get("PATH", "")
        logger.info("Using FFmpeg from %s", found)
        return

    logger.warning(
        "FFmpeg not found. Install it and add the bin folder to PATH "
        "(or set FFMPEG_PATH in .env)."
    )
