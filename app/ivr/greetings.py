from twilio.twiml.voice_response import VoiceResponse, Gather

from app.config import settings


GREETING_EN = "Welcome to our customer support line."
GREETING_AR = "مرحباً بك في خط دعم العملاء."
IVR_PROMPT_EN = "Press 1 for English. Press 2 for Arabic."
IVR_PROMPT_AR = "اضغط 1 للإنجليزية. اضغط 2 للعربية."
GOODBYE_EN = "Thank you for calling. Goodbye."
GOODBYE_AR = "شكراً لاتصالك. مع السلامة."
NO_INPUT_EN = "Sorry, I did not catch that. "
NO_INPUT_AR = "عذراً، لم أسمع ذلك. "
BUSY_EN = "All our agents are currently busy. Please try again later."
BUSY_AR = "جميع الوكلاء مشغولون حالياً. يرجى المحاولة مرة أخرى لاحقاً."


def build_ivr_response() -> str:
    response = VoiceResponse()
    gather = Gather(
        num_digits=1,
        timeout=settings.ivr_timeout_seconds,
        action=f"{settings.twilio_webhook_url}/ivr/selected",
        method="POST",
    )
    gather.say(GREETING_EN, language="en-US")
    gather.say(IVR_PROMPT_EN, language="en-US")
    response.append(gather)
    response.redirect(f"{settings.twilio_webhook_url}/ivr/timeout", method="POST")
    return str(response)


def build_language_greeting(language: str) -> str:
    response = VoiceResponse()
    if language == "ar":
        response.say(GREETING_AR, language="ar-XA")
    else:
        response.say(GREETING_EN, language="en-US")
    return str(response)


def build_goodbye(language: str) -> str:
    response = VoiceResponse()
    if language == "ar":
        response.say(GOODBYE_AR, language="ar-XA")
    else:
        response.say(GOODBYE_EN, language="en-US")
    response.hangup()
    return str(response)


def build_timeout_response(retry_count: int, language: str = "en") -> str:
    response = VoiceResponse()
    if retry_count >= settings.ivr_max_retries:
        if language == "ar":
            response.say(BUSY_AR, language="ar-XA")
        else:
            response.say(BUSY_EN, language="en-US")
        response.hangup()
        return str(response)

    if language == "ar":
        response.say(NO_INPUT_AR, language="ar-XA")
    else:
        response.say(NO_INPUT_EN, language="en-US")

    prompt = IVR_PROMPT_AR if language == "ar" else IVR_PROMPT_EN
    lang_attr = "ar-XA" if language == "ar" else "en-US"

    gather = Gather(
        num_digits=1,
        timeout=settings.ivr_timeout_seconds,
        action=f"{settings.twilio_webhook_url}/ivr/selected",
        method="POST",
    )
    gather.say(prompt, language=lang_attr)
    response.append(gather)
    response.redirect(
        f"{settings.twilio_webhook_url}/ivr/timeout?retry={retry_count + 1}",
        method="POST",
    )
    return str(response)
