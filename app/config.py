from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    twilio_webhook_url: str = ""

    app_host: str = "0.0.0.0"
    app_port: int = 8000
    environment: str = "development"
    log_level: str = "INFO"

    faq_data_dir: str = "./data/faq"

    chroma_persist_dir: str = "./data/chroma"
    chroma_collection: str = "faq_embeddings"

    whisper_model: str = "base"

    tts_voice_en: str = "en-US-AvaNeural"
    tts_voice_ar: str = "ar-SA-ZariyahNeural"

    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:1.5b"

    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_local_only: bool = False

    stt_sample_rate: int = 8000
    stt_language_en: str = "en"
    stt_language_ar: str = "ar"

    tts_sample_rate: int = 24000

    ffmpeg_path: str = ""

    ivr_timeout_seconds: int = 10
    ivr_max_retries: int = 2


settings = Settings()
