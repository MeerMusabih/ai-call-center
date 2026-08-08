import logging
import json
import httpx

from app.config import settings
from app.ai.prompts import get_system_prompt, get_greeting
from app.models.schemas import TranscriptEntry

logger = logging.getLogger(__name__)


class AzureOpenAIChat:
    """Azure OpenAI chat client, same interface as OllamaChat."""

    def __init__(self):
        self.endpoint = settings.azure_openai_endpoint.rstrip("/")
        self.deployment = settings.azure_openai_deployment
        self.api_key = settings.azure_openai_key
        self.api_version = settings.azure_openai_api_version
        self.client = httpx.AsyncClient(timeout=settings.azure_openai_timeout)

    @property
    def configured(self) -> bool:
        return bool(self.endpoint and self.api_key and self.deployment)

    def _build_messages(
        self,
        user_message: str,
        faq_context: str,
        transcript: list[TranscriptEntry],
        language: str,
    ) -> list[dict]:
        system_prompt = get_system_prompt(language).format(
            faq_context=faq_context,
            conversation_history="",
        )
        messages = [{"role": "system", "content": system_prompt}]

        for entry in transcript[-4:]:
            role = "user" if entry.role == "user" else "assistant"
            messages.append({"role": role, "content": entry.text})

        messages.append({"role": "user", "content": user_message})
        return messages

    async def generate_response(
        self,
        user_message: str,
        faq_context: str,
        transcript: list[TranscriptEntry],
        language: str,
    ) -> str:
        messages = self._build_messages(user_message, faq_context, transcript, language)

        url = f"{self.endpoint}/openai/deployments/{self.deployment}/chat/completions"
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }
        params = {"api-version": self.api_version}
        payload = {
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 48,
            "stream": True,
        }

        parts: list[str] = []
        async with self.client.stream(
            "POST", url, headers=headers, params=params, json=payload
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.strip() or not line.startswith("data:"):
                    continue
                data = line[len("data:"):].strip()
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk["choices"][0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        parts.append(content)
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue

        return "".join(parts).strip()

    async def get_initial_greeting(self, language: str) -> str:
        return get_greeting(language)
