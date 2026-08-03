import logging

from app.config import settings
from app.ai.gemini import OllamaChat
from app.ai.azure_openai import AzureOpenAIChat

logger = logging.getLogger(__name__)

LLM_PROVIDER_LOCAL = "local"
LLM_PROVIDER_AZURE = "azure_openai"


class HybridChat:
    """Chat client router: Azure OpenAI primary, local Ollama fallback.

    Selects the provider from LLM_PROVIDER in .env. In azure_openai mode,
    any Azure failure (missing credentials, network, timeout, HTTP error)
    automatically degrades to the local Ollama model.
    """

    def __init__(self):
        self.provider = settings.llm_provider.lower()
        self.azure = AzureOpenAIChat()
        self.local = OllamaChat()
        logger.info(f"LLM provider mode: {self.provider}")

    def _use_azure(self) -> bool:
        if self.provider != LLM_PROVIDER_AZURE:
            return False
        if not self.azure.configured:
            logger.warning(
                "LLM_PROVIDER=azure_openai but AZURE_OPENAI_* not configured; using local Ollama"
            )
            return False
        return True

    async def generate_response(
        self,
        user_message: str,
        faq_context: str,
        transcript,
        language: str,
    ) -> str:
        if self._use_azure():
            try:
                return await self.azure.generate_response(
                    user_message=user_message,
                    faq_context=faq_context,
                    transcript=transcript,
                    language=language,
                )
            except Exception as e:
                logger.warning(f"Azure OpenAI failed ({e}); falling back to local Ollama")

        return await self.local.generate_response(
            user_message=user_message,
            faq_context=faq_context,
            transcript=transcript,
            language=language,
        )

    async def get_initial_greeting(self, language: str) -> str:
        if self._use_azure():
            try:
                return await self.azure.get_initial_greeting(language)
            except Exception as e:
                logger.warning(f"Azure OpenAI greeting failed ({e}); falling back to local Ollama")
        return await self.local.get_initial_greeting(language)
