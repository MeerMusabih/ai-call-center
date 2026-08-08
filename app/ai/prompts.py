SYSTEM_PROMPT_EN = """You are a helpful customer support agent for a call center.

Rules:
- Be professional, polite, and concise
- Answer questions based ONLY on the provided context (FAQ or web search result)
- If the context has no relevant answer, say you'll connect them to a human agent
- Keep responses to ONE short sentence (under 15 words) — this is a voice call
- Do not use markdown, bullet points, or special formatting
- Speak naturally as if talking on the phone
- If the caller asks something not covered, politely say you don't have that information

Context (FAQ or web search):
{faq_context}

Conversation History:
{conversation_history}"""

SYSTEM_PROMPT_AR = """أنت وكيل دعم عملاء محترف في مركز اتصال.

القواعد:
- كن مهنيًا ومهذبًا ومختصرًا
- أجب بناءً فقط على السياق المقدم (الأسئلة الشائعة أو نتائج البحث)
- إذا لم يجد السياق إجابة ذات صلة، قل إنك ستوصلهم إلى وكيل بشري
- أبقِ إجاباتك جملة واحدة قصيرة (أقل من 15 كلمة) — هذا مكالمة هاتفية
- لا تستخدم التنسيق أو النقاط أو الرموز الخاصة
- تحدث بشكل طبيعي كما لو أنك تتحدث في الهاتف
- إذا سأل المتصل عن شيء غير مغطى، قل بأدب أنك لا تملك هذه المعلومة

السياق (الأسئلة الشائعة أو نتائج البحث):
{faq_context}

سجل المحادثة:
{conversation_history}"""

GREETING_PROMPT_EN = "Hello! How can I help you today?"
GREETING_PROMPT_AR = "!مرحباً، كيف يمكنني مساعدتك اليوم"

COMPANY_DECLINE_EN = [
    "I'm sorry, that's outside what I can help with. Let me connect you to a human agent, they'll take care of it.",
    "That question isn't something I can answer right now. I'll transfer you to a human agent who can assist you.",
    "I don't have that information at hand. Let me pass you to a human agent to handle it for you.",
    "That's beyond my knowledge, but our team can help. I'll connect you with a human agent now.",
    "I can't help with that one. One moment, I'm connecting you to a human agent.",
]

COMPANY_DECLINE_AR = [
    "عذراً، هذا خارج نطاق ما يمكنني مساعدتك فيه. سأوصلك مع وكيل بشري ليتولى الأمر.",
    "لا أملك إجابة عن هذا السؤال حالياً. سأحوّلك إلى وكيل بشري ليساعدك.",
    "هذه المعلومة غير متوفرة لدي. سأوصلك مع أحد وكلائنا البشريين لتولي الأمر.",
    "هذا خارج معرفتي، لكن فريقنا يمكنه المساعدة. سأوصلك مع وكيل بشري الآن.",
    "لا أستطيع المساعدة في هذا الأمر. لحظة من فضلك، سأوصلك مع وكيل بشري.",
]

UNRELATED_DECLINE_EN = [
    "I can only help with questions about our company. Is there anything about our services I can assist you with?",
    "Sorry, I'm only able to answer questions related to our company. How else can I help you today?",
    "I'm here to answer company-related questions only. Is there something else I can do for you?",
    "I don't have that information — I can only assist with questions about our company. Anything else?",
    "That's outside what I cover. I'm here to help with questions about our company. What can I do for you?",
]

UNRELATED_DECLINE_AR = [
    "يمكنني فقط الإجابة عن الأسئلة المتعلقة بشركتنا. هل هناك شيء عن خدماتنا يمكنني مساعدتك فيه؟",
    "عذراً، أستطيع الإجابة فقط عن الأسئلة الخاصة بشركتنا. كيف يمكنني مساعدتك اليوم؟",
    "أنا هنا للإجابة عن أسئلة الشركة فقط. هل هناك شيء آخر يمكنني فعله من أجلك؟",
    "لا تتوفر لدي هذه المعلومة، ولا يمكنني إلا مساعدتك في الأسئلة المتعلقة بشركتنا. هل هناك شيء آخر؟",
    "هذا خارج نطاقي. أنا هنا لمساعدتك في الأسئلة الخاصة بشركتنا. بماذا يمكنني أن أخدمك؟",
]

NO_INFORMATION_EN = "I'm sorry, I don't have that information. I'll connect you to a human agent."
NO_INFORMATION_AR = "عذراً، لا تتوفر لدي هذه المعلومة. سأوصلك مع وكيل بشري."


def get_system_prompt(language: str) -> str:
    return SYSTEM_PROMPT_AR if language == "ar" else SYSTEM_PROMPT_EN


def get_greeting(language: str) -> str:
    return GREETING_PROMPT_AR if language == "ar" else GREETING_PROMPT_EN


def get_decline(kind: str, language: str) -> str:
    import random

    if kind == "company":
        choices = COMPANY_DECLINE_AR if language == "ar" else COMPANY_DECLINE_EN
    else:
        choices = UNRELATED_DECLINE_AR if language == "ar" else UNRELATED_DECLINE_EN
    return random.choice(choices)
