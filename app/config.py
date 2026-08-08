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
    whisper_cpu_threads: int = 0
    stt_max_concurrency: int = 4

    tts_voice_en: str = "en-US-AvaNeural"
    tts_voice_ar: str = "ar-SA-ZariyahNeural"

    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:1.5b"

    llm_provider: str = "local"
    azure_openai_endpoint: str = ""
    azure_openai_key: str = ""
    azure_openai_deployment: str = "gpt-4o-mini"
    azure_openai_api_version: str = "2024-06-01"
    azure_openai_timeout: float = 30.0

    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_local_only: bool = False

    faq_max_distance: float = 0.35
    web_search_enabled: bool = True
    web_search_timeout: float = 5.0
    web_min_similarity: float = 0.42

    stt_sample_rate: int = 8000
    stt_language_en: str = "en"
    stt_language_ar: str = "ar"

    tts_sample_rate: int = 24000

    ffmpeg_path: str = ""

    ivr_timeout_seconds: int = 10
    ivr_max_retries: int = 2


settings = Settings()
