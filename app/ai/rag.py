import logging
from app.config import settings
from app.faq.store import FAQStore
from app.ai.router import HybridChat
from app.models.schemas import TranscriptEntry

logger = logging.getLogger(__name__)


class RAGPipeline:
    _COMPANY_PROTOTYPES_EN = [
        "What is your pricing?",
        "Do you offer discounts or promotions?",
        "How do I contact your company?",
        "What products and services do you offer?",
        "How do I get support?",
        "What are your company policies?",
        "How do I change or cancel my plan?",
        "Where are your offices located?",
        "Who are the people at your company?",
        "Can you integrate with our software?",
        "Do you have a mobile app?",
        "How do I file a complaint about your service?",
        "What is your phone number?",
        "Do you offer refunds?",
        "How many employees do you have?",
        "What languages does your support team speak?",
        "Do you have staff in other countries?",
        "Is there a contract or commitment period?",
        "How long does implementation take?",
        "Do you offer a product demo?",
        "Can I add more users to my plan?",
        "Do you have a help center or documentation?",
        "Who are your business partners?",
        "Are you available outside working hours?",
        "How many customers use your service?",
        "Can I talk to a human agent?",
    ]

    _COMPANY_PROTOTYPES_AR = [
        "كم سعر خدماتكم؟",
        "هل تقدمون خصومات أو عروضاً؟",
        "كيف أتواصل مع شركتكم؟",
        "ما هي منتجاتكم وخدماتكم؟",
        "كيف أحصل على الدعم؟",
        "ما هي سياسات شركتكم؟",
        "كيف أغير أو ألغي باقتي؟",
        "أين توجد مكاتبكم؟",
        "من هم الموظفون في شركتكم؟",
        "هل يمكنكم التكامل مع برنامجنا؟",
        "هل لديكم تطبيق للهاتف؟",
        "كيف أقدم شكوى عن خدمتكم؟",
        "ما هو رقم هاتفكم؟",
        "هل تقدمون استرداد الأموال؟",
        "كم عدد موظفيكم؟",
        "ما هي اللغات التي يتحدث بها فريق الدعم؟",
        "هل لديكم موظفون في دول أخرى؟",
        "هل يوجد عقد أو فترة التزام؟",
        "كم من الوقت يستغرق التنفيذ؟",
        "هل تقدمون عرضاً توضيحياً للمنتج؟",
        "هل يمكنني إضافة مستخدمين أكثر إلى باقتي؟",
        "هل لديكم مركز مساعدة أو توثيق؟",
        "من هم شركاؤكم التجاريون؟",
        "هل تتوفرون خارج ساعات العمل؟",
        "كم عدد العملاء الذين يستخدمون خدمتكم؟",
        "هل يمكنني التحدث مع موظف بشري؟",
    ]

    def __init__(self, faq_store=None):
        self.faq_store = faq_store or FAQStore()
        self.gemini = HybridChat()
        self._prototype_embeddings: dict[str, object] = {}

    async def process_message(
        self,
        user_message: str,
        transcript: list[TranscriptEntry],
        language: str,
    ) -> tuple[str, str]:
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
            source = "faq"
        else:
            from app.ai.prompts import get_decline

            kind = (
                "company"
                if await asyncio.to_thread(self._is_company_topic, user_message, language)
                else "unrelated"
            )
            return get_decline(kind, language), kind

        if not context:
            from app.ai.prompts import NO_INFORMATION_AR, NO_INFORMATION_EN

            return (
                NO_INFORMATION_AR if language == "ar" else NO_INFORMATION_EN,
                source,
            )

        response = await self.gemini.generate_response(
            user_message=user_message,
            faq_context=context,
            transcript=transcript,
            language=language,
        )

        t2 = _t.time()
        logger.info(f"[TIMING] llm={t2-t1:.2f}s total={t2-t0:.2f}s")

        return response, source

    def _format_faq_context(self, chunks: list[dict]) -> str:
        if not chunks:
            return "No relevant FAQ information found."

        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            question = chunk.get("question", "")
            answer = chunk.get("answer", "")
            context_parts.append(f"FAQ {i}:\nQ: {question}\nA: {answer}")

        return "\n\n".join(context_parts)

    def _is_company_topic(self, query: str, language: str) -> bool:
        import numpy as np

        embedding = self.faq_store.embeddings.get_single_embedding
        eq = np.array(embedding(query))
        best = 0.0
        for proto in self._company_prototypes(language):
            sim = float(
                np.dot(eq, proto) / (np.linalg.norm(eq) * np.linalg.norm(proto))
            )
            if sim > best:
                best = sim
        return best >= settings.company_sim_threshold

    def _company_prototypes(self, language: str):
        import numpy as np

        if language == "ar":
            texts = self._COMPANY_PROTOTYPES_AR
            key = "ar"
        else:
            texts = self._COMPANY_PROTOTYPES_EN
            key = "en"
        if self._prototype_embeddings.get(key) is None:
            self._prototype_embeddings[key] = np.array(
                [
                    self.faq_store.embeddings.get_single_embedding(text)
                    for text in texts
                ]
            )
        return self._prototype_embeddings[key]

    async def get_greeting(self, language: str) -> str:
        return await self.gemini.get_initial_greeting(language)
