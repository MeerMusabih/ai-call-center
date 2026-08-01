import logging
from app.faq.store import FAQStore
from app.ai.gemini import OllamaChat as GeminiChat
from app.models.schemas import TranscriptEntry

logger = logging.getLogger(__name__)


class RAGPipeline:
    def __init__(self, faq_store=None):
        self.faq_store = faq_store or FAQStore()
        self.gemini = GeminiChat()

    async def process_message(
        self,
        user_message: str,
        transcript: list[TranscriptEntry],
        language: str,
    ) -> str:
        import time as _t
        t0 = _t.time()

        faq_chunks = self.faq_store.search(
            query=user_message,
            language=language,
            top_k=2,
        )

        t1 = _t.time()
        logger.info(f"[TIMING] faq_search={t1-t0:.2f}s")

        faq_context = self._format_faq_context(faq_chunks)

        response = await self.gemini.generate_response(
            user_message=user_message,
            faq_context=faq_context,
            transcript=transcript,
            language=language,
        )

        t2 = _t.time()
        logger.info(f"[TIMING] llm={t2-t1:.2f}s total={t2-t0:.2f}s")

        return response

    def _format_faq_context(self, chunks: list[dict]) -> str:
        if not chunks:
            return "No relevant FAQ information found."

        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            question = chunk.get("question", "")
            answer = chunk.get("answer", "")
            context_parts.append(f"FAQ {i}:\nQ: {question}\nA: {answer}")

        return "\n\n".join(context_parts)

    async def get_greeting(self, language: str) -> str:
        return await self.gemini.get_initial_greeting(language)
