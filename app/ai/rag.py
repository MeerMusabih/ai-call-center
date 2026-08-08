import logging
from app.config import settings
from app.faq.store import FAQStore
from app.ai.router import HybridChat
from app.models.schemas import TranscriptEntry

logger = logging.getLogger(__name__)


class RAGPipeline:
    def __init__(self, faq_store=None):
        self.faq_store = faq_store or FAQStore()
        self.gemini = HybridChat()

    async def process_message(
        self,
        user_message: str,
        transcript: list[TranscriptEntry],
        language: str,
    ) -> str:
        import time as _t
        import asyncio
        t0 = _t.time()

        faq_chunks, distances = await asyncio.to_thread(
            self.faq_store.search_with_scores,
            user_message,
            language,
            top_k=2,
        )

        t1 = _t.time()
        logger.info(f"[TIMING] faq_search={t1-t0:.2f}s")

        best_distance = min(distances) if distances else float("inf")

        if best_distance <= settings.faq_max_distance:
            context = self._format_faq_context(faq_chunks)
        elif settings.web_search_enabled:
            from app.ai.websearch import search as web_search

            t_search = _t.time()
            snippet = await web_search(user_message, language)
            logger.info(f"[TIMING] web_search={_t.time()-t_search:.2f}s")
            relevant = language == "en" and await asyncio.to_thread(
                self._is_relevant, user_message, snippet
            )
            if snippet and (relevant or language != "en"):
                context = f"[Web search result]\n{snippet}"
            else:
                context = ""
        else:
            context = ""

        if not context:
            from app.ai.prompts import NO_INFORMATION_AR, NO_INFORMATION_EN

            return NO_INFORMATION_AR if language == "ar" else NO_INFORMATION_EN

        response = await self.gemini.generate_response(
            user_message=user_message,
            faq_context=context,
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

    def _is_relevant(self, query: str, snippet: str) -> bool:
        import numpy as np

        embeddings = self.faq_store.embeddings.get_single_embedding
        eq = np.array(embeddings(query))
        es = np.array(embeddings(snippet))
        sim = float(np.dot(eq, es) / (np.linalg.norm(eq) * np.linalg.norm(es)))
        return sim >= settings.web_min_similarity

    async def get_greeting(self, language: str) -> str:
        return await self.gemini.get_initial_greeting(language)
