import logging
import httpx

from app.config import settings
from app.ai.prompts import get_system_prompt, get_greeting
from app.models.schemas import TranscriptEntry

logger = logging.getLogger(__name__)


class OllamaChat:
    def __init__(self):
        self.base_url = settings.ollama_url
        self.model = settings.ollama_model
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=120.0)
        logger.info(f"Ollama initialized: {self.model} at {self.base_url}")

    async def generate_response(
        self,
        user_message: str,
        faq_context: str,
        transcript: list[TranscriptEntry],
        language: str,
    ) -> str:
        system_prompt = get_system_prompt(language).format(
            faq_context=faq_context,
            conversation_history="",
        )

        messages = [{"role": "system", "content": system_prompt}]

        for entry in transcript[-4:]:
            role = "user" if entry.role == "user" else "assistant"
            messages.append({"role": role, "content": entry.text})

        messages.append({"role": "user", "content": user_message})

        response = await self.client.post(
            "/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": True,
                "keep_alive": -1,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 48,
                },
            },
        )

        response.raise_for_status()

        parts = []
        async for line in response.aiter_lines():
            if not line.strip():
                continue
            import json
            chunk = json.loads(line)
            if chunk.get("message", {}).get("content"):
                parts.append(chunk["message"]["content"])

        return "".join(parts).strip()

    async def get_initial_greeting(self, language: str) -> str:
        return get_greeting(language)
