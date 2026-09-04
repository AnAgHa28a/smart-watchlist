"""Generates the 'morning brief' narrative above the digest cards.

Built rule-based first and used as the default: this is a live-judged demo
and a flaky third-party LLM call should never be able to take down the
flagship feature. If ANTHROPIC_API_KEY is set, we layer a real LLM rewrite
on top — strictly grounded in the same computed facts (never given free rein
to invent numbers), with a hard timeout and automatic fallback to the
template on any failure.
"""
import logging

import httpx

from app.config import settings

logger = logging.getLogger("digest")

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


def _template_narrative(digest_items: list[dict], total_count: int, market_open: bool) -> str:
    if not digest_items:
        if total_count == 0:
            return "Your watchlist is empty — add a few symbols to start tracking what matters."
        return "Nothing crossed the bar since you last checked — everything's moving within its normal range."

    n = len(digest_items)
    plural = "stock" if n == 1 else "stocks"
    lead = f"{n} of {total_count} {plural} moved meaningfully since you last checked."

    top = digest_items[:3]
    sentences = []
    for item in top:
        tag = ""
        if item.get("sector_label") == "sector-wide":
            tag = " — sector-wide move, likely market noise"
        elif item.get("sector_label") == "idiosyncratic":
            tag = " — moving alone against its sector, worth a look"
        sentences.append(f"{item['symbol']} {item['explanation'].rstrip('.')}{tag}.")

    market_note = "" if market_open else " Markets are closed — these reflect the last session."
    return lead + market_note + " " + " ".join(sentences)


async def _llm_rewrite(template: str, digest_items: list[dict]) -> str | None:
    if not settings.anthropic_api_key:
        return None
    facts = "\n".join(f"- {i['symbol']}: {i['explanation']}" for i in digest_items[:5])
    prompt = (
        "Rewrite the following market watchlist brief in 2-3 crisp sentences, "
        "for a retail investor. Do NOT invent any numbers, sectors, or facts "
        "not present below. Keep it factual and concise, no hype.\n\n"
        f"Draft: {template}\n\nGrounding facts:\n{facts}"
    )
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                ANTHROPIC_URL,
                headers={
                    "x-api-key": settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 200,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            text = "".join(block.get("text", "") for block in data.get("content", []))
            return text.strip() or None
    except Exception as e:
        logger.info(f"LLM digest rewrite unavailable, using template: {e}")
        return None


async def generate_digest_narrative(digest_items: list[dict], total_count: int, market_open: bool) -> str:
    template = _template_narrative(digest_items, total_count, market_open)
    if not digest_items or not settings.anthropic_api_key:
        return template
    rewritten = await _llm_rewrite(template, digest_items)
    return rewritten or template
