"""
LLM Client — abstraction layer for Gemini Flash (google-genai SDK).

Usage:
    from app.services.llm_client import generate_text, LLMError

    result = generate_text(prompt, max_tokens=800)
    # Returns str on success, raises LLMError on failure after retries.

Fallback:
    If GEMINI_API_KEY is not set, or quota/network errors occur after retries,
    LLMError is raised and callers must fall back to rule-based templates.
    If the primary model is retired (404) or overloaded (5xx), the call is
    retried once on LLM_FALLBACK_MODEL before giving up.

Config (env vars):
    GEMINI_API_KEY        — required for LLM calls
    LLM_MODEL             — default: gemini-3.5-flash
    LLM_FALLBACK_MODEL    — default: gemini-3.5-flash-lite ("" disables)
    LLM_THINKING_BUDGET   — default: 1024 thinking tokens, added ON TOP of
                            max_tokens so reasoning never starves the answer
    LLM_MAX_RETRIES       — default: 1 (conservative to save quota)
    LLM_TIMEOUT           — default: 45 seconds per API call

Cost tracking:
    Every successful call logs its token counts and an estimated cost, and
    fills the optional `usage_out` dict so callers can store it next to what
    they generated (ad analysis keeps it in the cached blob as `_llm_usage`).

History: gemini-2.5-flash was retired for new keys (404) in late 2026, and the
old google-generativeai SDK reached end-of-life — both silently pushed every
caller onto template fallbacks. This module now uses google-genai only.
"""

import json
import logging
import os
import re
import time
from typing import Any

logger = logging.getLogger(__name__)

_MODEL          = os.getenv("LLM_MODEL", "gemini-3.5-flash")
_FALLBACK_MODEL = os.getenv("LLM_FALLBACK_MODEL", "gemini-3.5-flash-lite")
_THINKING       = int(os.getenv("LLM_THINKING_BUDGET", "1024"))
_RETRIES        = int(os.getenv("LLM_MAX_RETRIES", "1"))  # reduced: save quota on free tier
_API_KEY        = os.getenv("GEMINI_API_KEY", "")
_TIMEOUT        = int(os.getenv("LLM_TIMEOUT", "45"))  # seconds per API call

# List prices in USD per 1M tokens (input, output), for the cost estimate only.
# Thinking tokens bill as output. Figures from public price trackers (Nov 2026)
# — check https://ai.google.dev/gemini-api/docs/pricing before relying on them.
_PRICES_USD_PER_M: dict[str, tuple[float, float]] = {
    "gemini-3.5-flash-lite": (0.30, 2.50),
    "gemini-3.5-flash":      (1.50, 9.00),
}

# Lazy-initialised client — avoids import errors when SDK not installed
_client: Any = None

# Quota cooldown: when we get a 429, stop retrying for this many seconds
_quota_exhausted_until: float = 0.0

# Search grounding is metered separately (and may have no free-tier allowance).
# A grounding 429 only pauses grounding — callers fall back to closed-book.
_GROUNDING_COOLDOWN = int(os.getenv("LLM_GROUNDING_COOLDOWN", "1800"))
_grounding_unavailable_until: float = 0.0


class LLMError(Exception):
    """Raised when LLM call fails after all retries."""
    pass


class QuotaExhaustedError(LLMError):
    """Raised specifically when the API quota is exhausted (429)."""
    pass


def _get_client():
    global _client
    if _client is None:
        if not _API_KEY:
            raise LLMError("GEMINI_API_KEY not set")
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            raise LLMError("google-genai package not installed")
        _client = genai.Client(
            api_key=_API_KEY,
            http_options=types.HttpOptions(timeout=_TIMEOUT * 1000),
        )
    return _client


def _is_quota_error(e: Exception) -> bool:
    s = str(e)
    return "429" in s or "RESOURCE_EXHAUSTED" in s or "ResourceExhausted" in type(e).__name__


def _is_model_unavailable(e: Exception) -> bool:
    """Retired model (404) or server-side capacity (5xx) — worth trying the fallback."""
    s = str(e)
    return bool(re.search(r"\b(404|500|502|503|504)\b", s)) or "NOT_FOUND" in s \
        or "UNAVAILABLE" in s or "DEADLINE_EXCEEDED" in s


def _enter_quota_cooldown(e: Exception) -> None:
    global _quota_exhausted_until
    cooldown = 60
    m = re.search(r"retry in (\d+)", str(e), re.IGNORECASE)
    if m:
        cooldown = int(m.group(1)) + 5  # add buffer
    _quota_exhausted_until = time.monotonic() + cooldown
    print(f"[LLM] Gemini quota exhausted — cooldown {cooldown}s.")


def _models_to_try() -> list[str]:
    models = [_MODEL]
    if _FALLBACK_MODEL and _FALLBACK_MODEL != _MODEL:
        models.append(_FALLBACK_MODEL)
    return models


def _extract_text(response) -> str:
    """Return the response text, or raise LLMError explaining why there is none."""
    if not getattr(response, "candidates", None):
        fb = getattr(response, "prompt_feedback", None)
        raise LLMError(f"Gemini blocked response: {getattr(fb, 'block_reason', 'unknown')}")
    text = (getattr(response, "text", None) or "").strip()
    if not text:
        reason = getattr(response.candidates[0], "finish_reason", "unknown")
        raise LLMError(f"Empty response from Gemini (finish_reason={reason})")
    return text


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float | None:
    """Estimated list-price cost of one call; None for a model we have no price for."""
    # Longest matching prefix, so dated variants ("…-flash-lite-001") resolve
    # and "-flash-lite" is never priced as "-flash".
    for name in sorted(_PRICES_USD_PER_M, key=len, reverse=True):
        if model.startswith(name):
            p_in, p_out = _PRICES_USD_PER_M[name]
            return round((input_tokens * p_in + output_tokens * p_out) / 1_000_000, 6)
    return None


def _usage_from(response, model: str) -> dict:
    """Token counts and estimated cost of one response (zeros if the SDK gave none)."""
    um = getattr(response, "usage_metadata", None)
    inp = int(getattr(um, "prompt_token_count", 0) or 0)
    out = int(getattr(um, "candidates_token_count", 0) or 0)
    think = int(getattr(um, "thoughts_token_count", 0) or 0)
    # If the SDK reports a total above what it itemised, the gap is billed
    # output we would otherwise miss (e.g. reasoning reported only in the total).
    total = int(getattr(um, "total_token_count", 0) or 0)
    think = max(think, total - inp - out)
    return {
        "model": model,
        "input_tokens": inp,
        "output_tokens": out,
        "thinking_tokens": think,
        "cost_usd": estimate_cost_usd(model, inp, out + think),
    }


def generate_text(prompt: str, max_tokens: int = 1024, usage_out: dict | None = None) -> str:
    """
    Call Gemini and return the response text.
    Retries up to LLM_MAX_RETRIES times on transient errors, then falls back to
    LLM_FALLBACK_MODEL if the primary is retired/overloaded.
    Raises LLMError on failure, QuotaExhaustedError on 429.

    `usage_out`, if given, is filled with the tokens and estimated cost of the
    call that produced the answer.
    """
    now = time.monotonic()
    if now < _quota_exhausted_until:
        remaining = int(_quota_exhausted_until - now)
        raise QuotaExhaustedError(f"Gemini quota cooldown active ({remaining}s remaining).")

    client = _get_client()
    from google.genai import types

    # Thinking models spend output budget on reasoning; give the answer its own
    # max_tokens and add the thinking budget on top.
    config = types.GenerateContentConfig(
        max_output_tokens=max_tokens + max(_THINKING, 0),
        temperature=0.7,
        thinking_config=types.ThinkingConfig(thinking_budget=max(_THINKING, 0)),
    )

    last_err: Exception | None = None
    for model in _models_to_try():
        for attempt in range(_RETRIES + 1):
            try:
                resp = client.models.generate_content(model=model, contents=prompt, config=config)
                text = _extract_text(resp)
                usage = _usage_from(resp, model)
                cost = usage["cost_usd"]
                print(f"[LLM] usage model={model} in={usage['input_tokens']} "
                      f"out={usage['output_tokens']} thinking={usage['thinking_tokens']} "
                      f"cost_usd={'?' if cost is None else f'{cost:.4f}'}")
                if usage_out is not None:
                    usage_out.update(usage)
                return text
            except LLMError as e:
                last_err = e          # blocked / empty — not transient, try next model
                break
            except Exception as e:
                last_err = e
                if _is_quota_error(e):
                    _enter_quota_cooldown(e)
                    raise QuotaExhaustedError(f"Gemini API quota exceeded: {str(e)[:160]}")
                print(f"[LLM] {model} attempt {attempt + 1}/{_RETRIES + 1} failed: "
                      f"{type(e).__name__}: {str(e)[:200]}")
                if _is_model_unavailable(e):
                    break             # retrying the same unavailable model won't help
                if attempt < _RETRIES:
                    time.sleep(2.0 * (attempt + 1))

    raise LLMError(f"Gemini failed: {type(last_err).__name__}: {last_err}")


def _strip_fences(text: str) -> str:
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return text.strip()


def generate_json(prompt: str, max_tokens: int = 1024, usage_out: dict | None = None) -> dict:
    """
    Call Gemini expecting JSON output. Strips markdown fences if present.
    Raises LLMError if response cannot be parsed as JSON.
    """
    text = _strip_fences(generate_text(prompt, max_tokens=max_tokens, usage_out=usage_out))
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise LLMError(f"Gemini returned invalid JSON: {e}\nRaw: {text[:300]}")


def generate_grounded(prompt: str) -> tuple[str, list[str]]:
    """
    Call Gemini WITH Google Search grounding, so the model researches live
    sources instead of answering from memory.

    Returns (text, source_urls). Raises LLMError if grounding is unavailable or
    fails — the caller is expected to fall back to closed-book generate_json().
    This is the 'tool' the Curator agent's research step uses.
    """
    global _grounding_unavailable_until
    if not _API_KEY:
        raise LLMError("GEMINI_API_KEY not set")
    if time.monotonic() < _grounding_unavailable_until:
        raise LLMError("grounding paused after quota error — use closed-book")
    try:
        from google.genai import types
    except ImportError:
        raise LLMError("google-genai not installed (grounding unavailable)")

    client = _get_client()
    config = types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())],
        temperature=0.3,
    )

    resp, last_err = None, None
    for model in _models_to_try():
        try:
            resp = client.models.generate_content(model=model, contents=prompt, config=config)
            break
        except Exception as e:
            last_err = e
            if _is_quota_error(e):
                # Grounding quota only — don't freeze plain generation.
                _grounding_unavailable_until = time.monotonic() + _GROUNDING_COOLDOWN
                print(f"[LLM] grounding quota exhausted — closed-book for {_GROUNDING_COOLDOWN}s")
                raise LLMError(f"grounding quota exceeded: {str(e)[:120]}")
            if not _is_model_unavailable(e):
                break
    if resp is None:
        raise LLMError(f"grounded call failed: {type(last_err).__name__}: {last_err}")

    text = (getattr(resp, "text", None) or "").strip()
    if not text:
        raise LLMError("empty grounded response")

    # Pull the source URLs Gemini actually cited (grounding metadata).
    sources: list[str] = []
    try:
        gm = resp.candidates[0].grounding_metadata
        for ch in (getattr(gm, "grounding_chunks", None) or []):
            uri = getattr(getattr(ch, "web", None), "uri", None)
            if uri:
                sources.append(uri)
    except Exception:
        pass
    return text, sources


def llm_available() -> bool:
    """Quick check — returns True if GEMINI_API_KEY is configured."""
    return bool(_API_KEY)


def llm_selftest() -> str:
    """
    Run a minimal Gemini call to verify the API key and model work.
    Returns a short status string. Only call on-demand (costs 1 API call).
    """
    if not _API_KEY:
        return "skip:no_api_key"
    try:
        result = generate_text("Responde apenas com a palavra OK.", max_tokens=10)
        return f"ok:model={_MODEL},response={result[:30]}"
    except QuotaExhaustedError as e:
        return f"quota_exhausted:{e}"
    except LLMError as e:
        return f"fail:{e}"
    except Exception as e:
        return f"error:{type(e).__name__}:{e}"
