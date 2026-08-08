import logging
import re
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

DDG_API = "https://api.duckduckgo.com/"
WIKI_API = "https://{lang}.wikipedia.org/w/api.php"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"

MAX_SNIPPET_CHARS = 900

_client = httpx.AsyncClient(
    timeout=settings.web_search_timeout,
    headers={"User-Agent": "ai-call-center-demo/1.0 (contact: support@example.com)"},
)

_EN_LEADING = re.compile(
    r"^(what|what's|whats|who|who's|whose|when|where|which|why|how|"
    r"do|does|did|is|are|was|were|can|could|would|should|tell me|find)\b\s*",
    re.I,
)
_AR_LEADING = re.compile(
    r"^(ما هي|ما هو|ما|من هو|من هي|من|أين|متى|كيف|كم|هل|أخبرني عن|عرفني على)\s*"
)


def clean_query(query: str) -> str:
    q = re.sub(r"[؟?.\s!]+$", "", query.strip()).strip()
    for rx in (_EN_LEADING, _AR_LEADING, _EN_LEADING):
        q = rx.sub("", q).strip()
    return q.strip()


def _truncate(text: str, limit: int = MAX_SNIPPET_CHARS) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "…"


async def _ddg_instant_answer(query: str, language: str) -> str:
    """DuckDuckGo Instant Answer API — free, no API key required."""
    params = {
        "q": query,
        "format": "json",
        "no_html": 1,
        "skip_disambig": 1,
        "no_redirect": 1,
        "kl": "ar-sa" if language == "ar" else "us-en",
    }
    resp = await _client.get(DDG_API, params=params)
    resp.raise_for_status()
    data = resp.json()

    parts = []
    abstract = (data.get("AbstractText") or "").strip()
    answer = (data.get("Answer") or "").strip()
    if abstract:
        parts.append(abstract)
    if answer:
        parts.append(answer)

    for topic in (data.get("RelatedTopics") or [])[:3]:
        if "Topics" in topic:
            for sub in (topic.get("Topics") or [])[:2]:
                text = (sub.get("Text") or "").strip()
                if text:
                    parts.append(text)
        else:
            text = (topic.get("Text") or "").strip()
            if text:
                parts.append(text)

    if not parts:
        return ""
    return _truncate(" ".join(parts))


async def _wikipedia(query: str, language: str) -> str:
    """Wikipedia API — free, no API key required."""
    lang_code = "ar" if language == "ar" else "en"
    base = WIKI_API.format(lang=lang_code)

    resp = await _client.get(base, params={
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": 1,
        "format": "json",
        "origin": "*",
    })
    resp.raise_for_status()
    search = resp.json().get("query", {}).get("search") or []
    if not search:
        return ""
    title = search[0]["title"]

    resp = await _client.get(base, params={
        "action": "query",
        "prop": "extracts",
        "explaintext": 1,
        "exintro": 1,
        "titles": title,
        "format": "json",
        "origin": "*",
    })
    resp.raise_for_status()
    for page in resp.json().get("query", {}).get("pages", {}).values():
        extract = (page.get("extract") or "").strip()
        if extract:
            return _truncate(extract)
    return ""


async def _wikidata_capital(entity: str, language: str) -> str:
    """Capital-of lookup via Wikidata — precise and free, works in any language."""
    lang_code = "ar" if language == "ar" else "en"

    resp = await _client.get(WIKIDATA_API, params={
        "action": "wbsearchentities",
        "search": entity,
        "language": lang_code,
        "uselang": lang_code,
        "format": "json",
        "type": "item",
        "limit": 1,
    })
    resp.raise_for_status()
    hits = resp.json().get("search") or []
    if not hits:
        return ""
    qid = hits[0]["id"]
    entity_label = hits[0].get("label") or entity

    resp = await _client.get(WIKIDATA_API, params={
        "action": "wbgetentities",
        "ids": qid,
        "props": "claims",
        "format": "json",
    })
    resp.raise_for_status()
    claims = resp.json()["entities"][qid]["claims"]
    if "P36" not in claims:
        return ""
    capital_id = claims["P36"][0]["mainsnak"]["datavalue"]["value"]["id"]

    resp = await _client.get(WIKIDATA_API, params={
        "action": "wbgetentities",
        "ids": capital_id,
        "props": "labels",
        "languages": lang_code,
        "format": "json",
    })
    resp.raise_for_status()
    capital_label = resp.json()["entities"][capital_id]["labels"].get(
        lang_code, {}
    ).get("value", capital_id)

    if language == "ar":
        return f"عاصمة {entity_label} هي {capital_label}."
    return f"The capital of {entity_label} is {capital_label}."


def _capital_entity(query: str, cleaned: str) -> str:
    m = re.search(r"\bcapital of (.+?)[?.!]*$", query, re.I)
    if m:
        return m.group(1).strip()
    if cleaned.startswith("عاصمة"):
        rest = cleaned[len("عاصمة"):].strip()
        if rest:
            return rest
    return ""


async def search(query: str, language: str = "en") -> str:
    """Free web-search fallback. Returns a short context snippet, or '' if nothing found."""
    cleaned = clean_query(query)

    entity = _capital_entity(query, cleaned)
    if entity:
        try:
            text = await _wikidata_capital(entity, language)
            if text:
                return text
        except Exception as e:
            logger.warning(f"Wikidata search failed: {e}")

    try:
        for candidate in (cleaned, query):
            text = await _ddg_instant_answer(candidate, language)
            if text:
                return text
    except Exception as e:
        logger.warning(f"DDG search failed: {e}")

    try:
        for candidate in (cleaned, query):
            text = await _wikipedia(candidate, language)
            if text:
                return text
    except Exception as e:
        logger.warning(f"Wikipedia search failed: {e}")

    return ""
